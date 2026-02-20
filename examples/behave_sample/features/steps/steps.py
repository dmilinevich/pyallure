from behave import given, then, when


@given("numbers {a:d} and {b:d}")
def given_numbers(context, a, b):
    context.a = a
    context.b = b


@when("I add them")
def add(context):
    context.result = context.a + context.b


@then("result is {c:d}")
def check(context, c):
    assert context.result == c
