import enum
import json


class DatetimeType(enum.Enum):
    EXACT = -1
    DURATION = [-1, -1]
    CRONTIME = [-1, -1, -1, -1, -1]

    def __str__(self) -> str:
        return self.name.lower()


class DatetimeToken():

    def __init__(self, type: DatetimeType, text: str, span: tuple, value=None):
        self.type = type
        self.text = text
        self.span = span
        self.value = value if value else type.value

    def __str__(self) -> str:
        formatted = {'type': self.type, 'text': self.text,
                     'span': self.span, 'value': self.value}
        return json.dumps(formatted)


def is_leq_span(s1: list, s2: list):
    assert len(s1) == len(s2) == 2
    if s1[0] <= s2[0]:
        return True
    elif s2[0] < s1[0]:
        return False
    else:
        if s1[1] <= s2[1]:
            return True
        else:
            return False


def group_date_time(date_spans: list, time_spans: list):
    date_time_dict = {}
    # For each date assign the related times
    return date_time_dict


def det_type(text: str):
    # TODO Regex, pattern ....
    type = None
    return type


def evaluate_datetime(date_txt: str, time_txt: str):
    # Evaluate the aboslute value of the corresponding date and time 
    return 

def evaluate_crontime(date_txt: str):
    return
