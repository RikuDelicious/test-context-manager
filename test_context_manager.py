import inspect
import re

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

import contextlib


class SomeClass:
    def run(self):
        print("run")


@contextlib.contextmanager
def some_generator():
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
        with some_generator() as some:
            some.run()
            raise ValueError("ValueError occured.")
        print("@end with block")


# 以下、ジェネレータとcontextlib.contextmanagerデコレータについての解説
########################################################################################


@contextlib.contextmanager
def example_generator():
    print('code before yield "hoge"')
    yield "hoge"
    print('code after yield "hoge"')


def test_contextlib_contextmanager_1():
    """
    contextlib.contextmanager 関数
    この関数をyield文を使うジェネレータ関数のデコレータとして使うと、
    そのジェネレータ関数はジェネレータオブジェクトではなく、
    __enter__()と__enter__()を実装したコンテキストマネージャを返すようになる

    コンテキストマネージャとは、
    contextlib.AbstractContextManager抽象クラスを実装するオブジェクトである

    ※contextlib.contextmanager 関数でデコレートするジェネレータ関数は、
    必ず値を1つyieldしなければならない
    """
    cm = example_generator()
    assert isinstance(cm, contextlib.AbstractContextManager)
    assert (
        re.match(r"<contextlib._GeneratorContextManager object at 0x.{12}>", repr(cm))
        is not None
    )


def test_contextlib_contextmanager_2(capsys):
    """
    contextlib.contextmanagerでデコレートしたジェネレータ関数から
    返されるコンテキストマネージャをwith文で使うと、
    以下のような流れで処理が行われる。

    1. まず、ジェネレータ関数内のyield文までの処理が実行され、
    2. with文のasで指定した変数にyield式の値が渡される
    3. その後、withブロック内の処理が実行され、
    4. withブロックを抜けると、ジェネレータ関数内のyield文の後から処理が再開される

    本テストコードでは以下のテキストが標準出力される
    @start with block
    code before yield "hoge"
    code in with block
    value hoge was passed from yield statement
    code after yield "hoge"
    @end with block
    """
    cm = example_generator()
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with cm as yielded:
            print("code in with block")
            print(f"value {yielded} was passed from yield statement")
        print("@end with block")


def test_contextlib_contextmanager_3(capsys):
    """
    注意点1
    withブロック内で例外が発生し、かつ処理していない場合、
    その時点でジェネレータ関数内のyield文の箇所に制御が戻り、
    再度同じ例外が発生する（その後withブロックに制御は戻らない）

    この時、ジェネレータ関数側で例外を処理しなければ
    withブロックの外側に例外が再送出される。
    また、yield文の後のコードは実行されない。

    このテストコードでは以下のテキストが標準出力される。
    @start with block
    code before yield "hoge"
    code before exception in with block
    """
    cm = example_generator()
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with pytest.raises(Exception):  # Exception例外を捕捉
            with cm:
                print("code before exception in with block")
                raise Exception()  # yield "hoge" で再度Exception()が発生
                print("code after exception in with block")  # 実行されない
            print("@end with block")  # 実行されない


@contextlib.contextmanager
def example_generator_handle_exception():
    print('code before yield "hoge"')
    try:
        yield "hoge"
    except Exception:
        print("catching exception in generator function")
    finally:
        print('code after yield "hoge" in finally block')


def test_contextlib_contextmanager_4(capsys):
    """
    withブロック内で発生した例外をジェネレータ関数側で処理するには、
    yield文をtry...except構文で囲む。

    この時、exceptブロックから例外を再送出しない場合、
    withブロックに例外が処理済みであることが伝えられ、
    withブロックを抜けた直後のコードから実行を再開する。

    exceptブロックから例外を再送出する場合は、
    test_contextlib_contextmanager_3の場合と同様に、
    withブロックの外側に例外が送出される

    また、yield文の後のコードをfinallyブロックに移すことで、
    例外発生の有無にかかわらず確実に後処理を実行させることができる
    （リソースの開放処理など）

    このテストコードでは以下のテキストが標準出力される
    @start with block
    code before yield "hoge"
    code before exception in with block
    Catching exception in generator function
    code after yield "hoge" in finally block
    @end with block
    """
    cm = example_generator_handle_exception()
    with capsys.disabled():
        print_stdout_header()
        print("@start with block")
        with cm:
            print("code before exception in with block")
            raise Exception()  # yield "hoge" で再度Exception()が発生
            print("code after exception in with block")  # 実行されない
        print("@end with block")

@contextlib.contextmanager
def example_generator_handle_exception_re_raise():
    try:
        yield "hoge"
    except Exception:
        raise Exception("re-raise")
    finally:
        print('code after yield "hoge" in finally block')

def test_contextlib_contextmanager_5(capsys):
    """
    withブロック内で発生した例外をジェネレータ関数側で捕捉して
    再送出する場合のテスト
    """
    cm = example_generator_handle_exception_re_raise()
    with pytest.raises(Exception, match="re-raise"):
        with cm:
            raise Exception("raise from with block")