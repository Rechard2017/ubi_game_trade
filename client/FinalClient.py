# import sys
# sys.path.append('/root/FinalClient')

import grpc
import time
import numpy as np
import pandas as pd
import pickle

import question.question_pb2 as dealer_pb2
import question.question_pb2_grpc as rpc
import contest.contest_pb2 as answer_pb2
import contest.contest_pb2_grpc as answer_rpc
from lib.simple_logger import simple_logger

class Client(object):
    def __init__(self, userid: int, userpin: str, logger, address='47.100.97.93', broadport=40722, ansport=40723):
        self.userid = userid
        self.userpin = userpin
        # create a gRPC channel + stub
        self.address = address
        self.broadport = broadport
        self.ansport = ansport
        channel1 = grpc.insecure_channel(address + ':' + str(broadport))
        channel2 = grpc.insecure_channel(address + ':' + str(ansport))
        self.conn1 = rpc.QuestionStub(channel1)
        self.conn2 = answer_rpc.ContestStub(channel2)

        self.logger = logger
        self.history_list = []

        # 输出存储
        self.date_list = []
        self.all_position_list = []
        self.all_submit_position_list = []
        self.result_list = []
        self.aum = 0

        self.init_capital = -1
        self.today_return = 0
        self.return_list = []
        self.has_next_question = True
        self.session_key = -1
        self.sequence = 0
        self.next_sequence = 0
        self.capital = -1
        self.dailystk = -1
        self.positions = -1
        self.position_list = []
        self.position_maintain = np.array([0] * 500)
        self.today_data = pd.DataFrame()
        self.data_list = []
        self.yestoday_factor = pd.DataFrame()

        self.commission_rate = 0.0005
        self.minimum_commission = 0

        self.bidasks = []
        self.prices = []
        self.IC_list = []


        # 初始化列表
        columns = ['sequence', 'stock', 'open', 'high', 'low', 'close', 'volume', 'tvr']
        for i in range(1, 11):
            columns.append('bid%d_price' % i)
            columns.append('bid%d_volume' % i)
        for i in range(1, 11):
            columns.append('ask%d_price' % i)
            columns.append('ask%d_volume' % i)

        self.data_columns = columns

        if self.logger is None:
            self.logger = simple_logger()

        self.stoped = False
        self.login(self.userid, self.userpin)  # 这里是阻塞的，不登录无法进行游戏

    def __del__(self):
        self._is_started = False

    def login(self, user_id, user_pin):
        while True:
            try:
                request = answer_pb2.LoginRequest()
                request.user_id = user_id
                request.user_pin = user_pin
                self.logger.info('waiting for connect')
                response = self.conn2.login(request)

                if response:
                    if response.success:
                        self.init_capital = response.init_capital
                        self.asset = self.init_capital
                        self.session_key = response.session_key
                        self.logger.info('login success')
                        self.logger.info("init_capital" + str(self.init_capital))
                        self.logger.info("session_key" + str(self.session_key))
                        return
                    else:
                        self.logger.info('login failed.' + response.reason)
                        time.sleep(0.1)

            except grpc.RpcError as error:
                self.logger.info('login failed. will retry one second later')
                time.sleep(1)

    def main(self):
        while True:
            try:
                questionrequest = dealer_pb2.QuestionRequest(user_id=self.userid, user_pin=self.userpin, session_key=self.session_key)
                self.logger.info(str(self.sequence) + 'questionrequest  connection success')
                break
            except grpc.RpcError as error:
                self.logger.info(str(self.sequence) + ' questionrequest  connection failed')
                time.sleep(0.1)

        while self.has_next_question:
            # 获取行情
            for response in self.conn1.get_question(questionrequest):
                if response:
                    self.logger.info('request ' + str(response.sequence) + ' success')
                    self.sequence = response.sequence
                    self.next_sequence = response.sequence + 1
                    self.has_next_question = response.has_next_question
                    self.capital = response.capital
                    self.dailystk = response.dailystk
                    self.positions = np.array(response.positions)
                    self.logger.info(str(self.sequence) + ' request success')
                    self.logger.info('today capital:' + str(self.capital))

                    if self.sequence % 240 == 0:
                        self.position_list = []
                        self.position_maintain = np.array([0] * 500)
                        self.data_list = []
                        self.aum = 0

                    # self.date_list.append(self.sequence)
                    # self.all_position_list.append(self.positions)

                    self.update_data()            # 更新最新数据
                    self.choose_position()        # 选股


                # 提交仓位
                try:
                    ansrequest = answer_pb2.AnswerMakeRequest(user_id=self.userid, user_pin=self.userpin, session_key=self.session_key,
                                                         sequence=self.sequence, bidasks=self.bidasks, prices=self.prices)
                    # start_time4 = time.time()
                    response = self.conn2.submit_answer_make(ansrequest)
                    # end_time4 = time.time()

                    if response:
                        if response.accepted:
                            self.logger.info(str(self.sequence) + 'successful submit')
                        else:
                            self.logger.info(str(self.sequence) + 'failed submit ' + response.reason)

                        self.sequence = self.next_sequence #更新sequence
                        # print("time4_calculate:", end_time4 - start_time4)

                except grpc.RpcError as error:
                    self.logger.info(str(self.sequence) + 'answer failed')

                # self.all_submit_position_list.append(self.bidasks.copy())
                self.data_list.append(self.today_data.copy())

        # 输出文件
        # self.result_list.append(self.date_list)
        # self.result_list.append(self.all_position_list)
        # self.result_list.append(self.all_submit_position_list)
        # self.result_list.append(self.return_list)
        # self.result_list.append(self.history_list)
        #
        # with open("E:\\result_7_28_14.pkl", "wb") as f:
        #     pickle.dump(self.result_list, f)

        return

    def update_data(self):
        temp_list = []
        for i in self.dailystk:
            temp_list.append(list(i.values))
        self.today_data = pd.DataFrame(np.array(temp_list), columns=self.data_columns)
        # 记录历史数据，算自己的因子的时候开
        # self.history_list.append(self.today_data)

    def choose_position(self):
        priority = 2
        delay = 20

        # 今日数据
        today_data = self.today_data.copy()
        today_data['choose'] = 0
        today_data['score'] = 0
        today_data.set_index('stock', drop=True, inplace=True)

        # 昨日数据
        if len(self.data_list) < 5:
            self.bidasks = np.array([0] * 500)
            self.prices = np.array(today_data['ask1_price'])
            return

        yestoday_data = self.data_list[-1].copy()
        yestoday_data.set_index('stock', drop=True, inplace=True)
        delay5_data = self.data_list[-5].copy()
        delay5_data.set_index('stock', drop=True, inplace=True)

        # 今日因子计算
        factor1_frame = (today_data['close'] - delay5_data['close']) / delay5_data['close']
        factor2_frame = (today_data['bid1_volume'] * today_data['bid1_price']) / (today_data['ask1_volume'] * today_data['ask1_price'])

        ask_amount_frame = pd.DataFrame(
            np.array(today_data[['ask1_price', 'ask2_price', 'ask3_price', 'ask4_price', 'ask5_price']]) * np.array(
                today_data[['ask1_volume', 'ask2_volume', 'ask3_volume', 'ask4_volume', 'ask5_volume']]),
            columns=['ask1_amount', 'ask2_amount', 'ask3_amount', 'ask4_amount', 'ask5_amount'], index=today_data.index)
        bid_amount_frame = pd.DataFrame(
            np.array(today_data[['bid1_price', 'bid2_price', 'bid3_price', 'bid4_price', 'bid5_price']]) * np.array(
                today_data[['bid1_volume', 'bid2_volume', 'bid3_volume', 'bid4_volume', 'bid5_volume']]),
            columns=['bid1_amount', 'bid2_amount', 'bid3_amount', 'bid4_amount', 'bid5_amount'], index=today_data.index)


        big_ask_amount = ask_amount_frame[(ask_amount_frame.T > ask_amount_frame.mean(axis=1)).T].fillna(0).sum(axis=1)
        small_ask_amount = ask_amount_frame[(ask_amount_frame.T < ask_amount_frame.mean(axis=1)).T].fillna(0).sum(axis=1)
        big_bid_amount = bid_amount_frame[(bid_amount_frame.T > bid_amount_frame.mean(axis=1)).T].fillna(0).sum(axis=1)
        small_bid_amount = bid_amount_frame[(bid_amount_frame.T < bid_amount_frame.mean(axis=1)).T].fillna(0).sum(
            axis=1)

        factor3_frame = (small_ask_amount / small_bid_amount) * (big_ask_amount / big_bid_amount)

        factor_frame = factor1_frame.rank(method='min', ascending=True) * 1 + factor2_frame.rank(method='min', ascending=False) * 0.8 + factor3_frame.rank(method='min', ascending=True) * 0.5

        # # IC 识别
        # if len(self.yestoday_factor) != 0:
        #     buy_return_frame = today_data['bid%d_price' % priority] / yestoday_data['ask%d_price' % priority] - 1
        #     sell_return_frame = today_data['ask%d_price' % priority] / yestoday_data['bid%d_price' % priority] - 1
        #     return_frame = buy_return_frame.copy()
        #     return_frame[buy_return_frame < 0] = sell_return_frame[buy_return_frame < 0]
        #     return_frame[(buy_return_frame < 0) & (sell_return_frame > 0)] = 0
        #     yestoday_factor = self.yestoday_factor
        #     ICframe = pd.concat([yestoday_factor.rank(method='min'), return_frame.rank(method='min')], axis=1)
        #     IC = (ICframe.corr('spearman')).iloc[0, 1]
        #     self.IC_list.append(IC)
        # else:
        #     self.IC_list.append(np.nan)
        #
        # # 更新数据
        # self.yestoday_factor = factor1_frame.copy()

        # 持仓变动
        # if len(self.IC_list) >= 10:
        #     signal = pd.Series(self.IC_list[-10:]).mean()
        #     print("signal:", signal)
        #     if signal >= 0.135:

        today_data['score'] = factor_frame.rank(method='min', ascending=True)
        valid_length = len(today_data['score'].dropna())

        choose_rate = 0.02
        choose_number = round(choose_rate * valid_length)

        sort_instrument = today_data['score'].dropna().sort_values(ascending=True)

        buy_list = list(sort_instrument.index[:choose_number])
        sell_list = list(sort_instrument.index[-choose_number:])

        buy_number = len(buy_list)
        sell_number = len(sell_list)
        today_data.loc[buy_list, 'choose'] = 1
        today_data.loc[sell_list, 'choose'] = -1

        # print(self.sequence, "buy:", buy_list)
        # print(self.sequence, "sell:", sell_list)

        # 仓位计算
        use_rate = 2
        use_money = self.capital * use_rate / delay
        each_money = use_money / (buy_number + sell_number)

        today_data['price'] = 0
        today_data['positions'] = 0

        today_data.loc[today_data['choose'] == 1, 'positions'] = each_money // today_data.loc[
            today_data['choose'] == 1, 'ask%d_price' % priority]
        today_data.loc[today_data['choose'] == -1, 'positions'] = - each_money // today_data.loc[
            today_data['choose'] == -1, 'bid%d_price' % priority]

        # if self.sequence % 240 >= 240 - delay:
        #     today_data['positions'] = 0

        self.logger.info(
            'submit_position: buy_number: ' + str(buy_number) + ' sell_number: ' + str(sell_number))
        self.logger.info(' asset:' + str(self.capital) + ' use_rate:' + str(use_rate))


        if len(self.position_list) >= delay:
            self.position_maintain = self.position_maintain + np.array(today_data['positions']) - np.array(self.position_list[-delay])
            today_data['positions_change'] = self.position_maintain - self.positions
        else:
            self.position_maintain = self.position_maintain + np.array(today_data['positions'])
            today_data['positions_change'] = self.position_maintain - self.positions
            self.aum = self.aum + use_money

        today_data.loc[today_data['positions_change'] > 0, 'price'] = today_data.loc[
            today_data['positions_change'] > 0, 'ask%d_price' % priority]
        today_data.loc[today_data['positions_change'] < 0, 'price'] = today_data.loc[
            today_data['positions_change'] < 0, 'bid%d_price' % priority]

        self.bidasks = np.array(today_data['positions_change'])
        self.prices = np.array(today_data['price'])
        self.position_list.append(today_data['positions'].copy())

        # print("position_values:", (abs(self.position_maintain) * np.array(today_data['close'])).sum())
        # print("change_position_values:", (abs(np.array(today_data['positions_change'])) * np.array(today_data['close'])).sum())
        # print("already_used_money:", self.aum, " () ", use_money)
        # print("length of position_list:", len(self.position_list))


if __name__ == '__main__':
    userid = 18
    user_pin = 'ZkwmtMIzM5'
    logger = simple_logger()

    c = Client(userid, user_pin, logger)
    c.main()