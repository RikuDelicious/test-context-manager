import inspect

import pytest

"""
コンテキストマネージャーを実装する方法
1. メソッドに __enter__() と __exit__() を持つクラスを定義する
2. ジェネレータとcontextlib.contextmanagerデコレータを使う
"""

# Helpers
########################################################################################

def print_stdout_header():
    caller_name = inspect.stack()[1].function
    print()
    print()
    print("\033[33m" + f"#### {caller_name}() stdout" + "\033[0m")


# 1. メソッドに __enter__() と __exit__() を持つクラスを定義する
########################################################################################

class ExampleClass:
    """
    このクラスのインスタンスがwithブロックのコンテキストマネージャとして使われた時、
    withブロックに入った直後に__enter__()メソッドが、
    withブロックを抜ける前に__exit__()メソッドが必ず実行される。
    """

    def __init__(self, ex_handled: bool = False):
        self.ex_handled = ex_handled
        print("__init__")

    def __enter__(self):
        """
        with文のasで渡す値をここで返す。
        """
        print("__enter__")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        3つの引数にはwithブロック内で発生する例外に関する情報が渡される。
        exc_type: 例外クラス
        exc_val: 例外の値
        exc_tb: トレースバックオブジェクト

        withブロックでは例外など何が起きてもブロックを抜ける時に必ず__exit__()が呼ばれる。
        その際に引数に例外の情報が渡され、このメソッド内で処理することができる。
        このメソッドを抜けると、発生した例外が投げられる。

        ただし、このメソッドがTrueを返す場合は、
        例外が処理済みであるとされ、例外が投げられない。
        """
        print(f"__exit__({exc_type}, {exc_val}, {exc_tb})")
        return self.ex_handled

    def run(self):
        print("run")


def test_use_ExampleClass_as_context_manager(capsys):
    """
    標準出力に以下の内容が出力される。
    @start with block
    __init__
    __enter__
    run
    __exit__(<class 'ValueError'>, ValueError occured., <traceback object at 0x000000000000>)
    @end with block
    """
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with ExampleClass(True) as example:
            assert isinstance(example, ExampleClass)
            example.run()
            raise ValueError("ValueError occured.")
        print("@end with block")

def test_context_manager_after_instantiate(capsys):
    """
    オブジェクト初期化後にコンテクストマネージャーとして使っても処理に変化はない
    """
    example_obj = ExampleClass(True)
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with example_obj as example:
            assert isinstance(example, ExampleClass)
            example.run()
            raise ValueError("ValueError occured.")
        print("@end with block")


# 2. ジェネレータとcontextlib.contextmanagerデコレータを使う
########################################################################################

from contextlib import contextmanager


class SomeClass:
    def run(self):
        print("run")

@contextmanager
def example_generator():
    """
    with文でこの関数をコンテキストマネージャとして使う。
    yield文までのコードがwithブロックに入った直後に実行され、
    yield文でasの後に渡す値を指定する。
    withブロックを抜けるとyield文の後のコードが実行される。
    """
    print("Starting")
    try:
        yield SomeClass()
    except ValueError as e:
        """
        withブロック内で発生する例外のハンドリング
        """
        print(e)
        print("Ignore Exception")
    except Exception as e:
        """
        withブロック内で発生する例外のハンドリング
        """
        print(e)
        print("Do not ignore exception")
        raise
    finally:
        """
        withブロックを抜けた後に必ず実行する処理
        """
        print("Exiting")

def test_contextmanager_generator(capsys):
    """
    標準出力に以下の内容が出力される。
    @start with block
    Starting
    run
    ValueError occured.
    Ignore Exception
    Exiting
    @end with block
    """
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with example_generator() as some:
            some.run()
            raise ValueError("ValueError occured.")
        print("@end with block")