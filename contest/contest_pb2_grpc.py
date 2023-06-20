# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import contest.contest_pb2 as contest__pb2


class ContestStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.login = channel.unary_unary(
                '/Contest/login',
                request_serializer=contest__pb2.LoginRequest.SerializeToString,
                response_deserializer=contest__pb2.UserLoginResponse.FromString,
                )
        self.submit_answer_make = channel.unary_unary(
                '/Contest/submit_answer_make',
                request_serializer=contest__pb2.AnswerMakeRequest.SerializeToString,
                response_deserializer=contest__pb2.AnswerMakeResponse.FromString,
                )


class ContestServicer(object):
    """Missing associated documentation comment in .proto file."""

    def login(self, request, context):
        """A user must first register and acquire a valid user ID and PIN and session key
        NOTE: every time you will get a random session key, all answer must submit along with this key
        this provent user login in multiply times and submit multiply answers
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def submit_answer_make(self, request, context):
        """Requests a full update with prices and changes in positions
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ContestServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'login': grpc.unary_unary_rpc_method_handler(
                    servicer.login,
                    request_deserializer=contest__pb2.LoginRequest.FromString,
                    response_serializer=contest__pb2.UserLoginResponse.SerializeToString,
            ),
            'submit_answer_make': grpc.unary_unary_rpc_method_handler(
                    servicer.submit_answer_make,
                    request_deserializer=contest__pb2.AnswerMakeRequest.FromString,
                    response_serializer=contest__pb2.AnswerMakeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Contest', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Contest(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def login(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Contest/login',
            contest__pb2.LoginRequest.SerializeToString,
            contest__pb2.UserLoginResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def submit_answer_make(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Contest/submit_answer_make',
            contest__pb2.AnswerMakeRequest.SerializeToString,
            contest__pb2.AnswerMakeResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
