import enum
import json
import re


class DatetimeType(enum.Enum):
    EXACT = -1
    DURATION = [-1, -1]
    CRONTIME = [-1, -1, -1, -1, -1]

    def __str__(self) -> str:
        return self.name.lower()


class TokenSpan:

    def __init__(self, span: str):
        list_form = span.strip('][').split(', ')
        assert len(list_form) == 2
        self.head = int(list_form[0])
        self.tail = int(list_form[1])
        self.list = span

    def __str__(self) -> str:
        return f'({self.head},{self.tail})'

    def contains(self, span: "TokenSpan") -> bool:
        return self.head <= span.head and (self.tail >= span.tail or self.tail == -1)

    def get_rhead(self, bhead: int = 0) -> "TokenSpan":
        return TokenSpan(f'[{bhead}, {self.head}]')

    def get_rtail(self, btail: int = -1) -> "TokenSpan":
        return TokenSpan(f'[{self.tail}, {btail}]')


class DatetimeToken:

    def __init__(self, dt_type: DatetimeType, text: str, span: TokenSpan, value=None):
        self.type = dt_type
        self.text = text
        self.span = span
        self.value = value if value else dt_type.value

    def __str__(self) -> str:
        formatted = {'type': self.type, 'text': self.text,
                     'span': self.span, 'value': self.value}
        return json.dumps(formatted)


def group_date_time(date_spans: list, time_spans: list):
    # For each date assign the related times
    date_time_dict = {}
    ds_dir = []
    j = 0
    for i in range(len(date_spans)):
        ds = TokenSpan(date_spans[i])
        time_list = []
        ds_dir.append(0)
        prev_tail = TokenSpan(date_spans[i - 1]).tail if i > 0 else 0
        next_head = TokenSpan(date_spans[i + 1]).head if i < len(date_spans) - 1 else -1
        for j in range(j, len(time_spans)):
            ts = TokenSpan(time_spans[j])
            if ds_dir[i] == 0:
                if ds.get_rhead(prev_tail).contains(ts):
                    ds_dir[i] = -1
                    time_list.append(ts.list)
                elif ds.get_rtail(next_head).contains(ts):
                    ds_dir[i] = 1
                    time_list.append(ts.list)
                # elif
            elif ds_dir[i] == -1:
                if ds.get_rhead(prev_tail).contains(ts):
                    time_list.append(ts.list)
            else:
                if ds.get_rtail(next_head).contains(ts):
                    time_list.append(ts.list)
        # j += 1
        date_time_dict[ds.list] = time_list
    return date_time_dict


def det_type(text: str) -> DatetimeType:
    # TODO Regex, pattern ....
    # duration_start_markers_rgx = 'از'
    # duration_end_markers_rgx = 'تا|لغایت|الی'
    # x = re.search(f"^.*({duration_start_markers_rgx}).*({duration_end_markers_rgx}).*$", text)
    # print(x)
    type: DatetimeToken
    return type


def evaluate_datetime(date_txt: str, time_txt: str):
    # Evaluate the aboslute value of the corresponding date and time
    return


def evaluate_crontime(date_txt: str):
    return
