import enum
import json
import re
import jdatetime
import datetime

import unidecode as unidecode
from dateutil import relativedelta

persian_months = {'فروردین': 1,
                  'اردیبهشت': 2,
                  'خرداد': 3,
                  'تیر': 4,
                  'مرداد': 5,
                  'شهریور': 6,
                  'مهر': 7,
                  'آبان': 8,
                  'آذر': 9,
                  'دی': 10,
                  'بهمن': 11,
                  'اسفند': 12}

persian_days = {'شنبه': (1, 'SAT'),
                'یکشنبه': (2, 'SUN'),
                'دوشنبه': (3, 'MON'),
                'سه‌شنبه': (4, 'TUS'),
                'چهارشنبه': (5, 'WED'),
                'پنجشنبه': (6, 'THU'),
                'جمعه': (7, 'FRI')}


class DatetimeType(enum.Enum):
    EXACT = -1
    DURATION = [-1, -1]
    CRONTIME = [-1, -1, -1, -1, -1]

    def __str__(self) -> str:
        return self.name.lower()

    def __repr__(self) -> str:
        return str(self)


class TokenSpan:

    def __init__(self, span: str):
        list_form = span.strip('][').split(', ')
        assert len(list_form) == 2
        self.head = int(list_form[0])
        self.tail = int(list_form[1])
        self.list = span

    def __str__(self) -> str:
        return f'({self.head},{self.tail})'

    def __repr__(self) -> str:
        return str(self)

    def contains(self, span: "TokenSpan") -> bool:
        return self.head <= span.head and (self.tail >= span.tail or self.tail == -1)

    def get_rhead(self, bhead: int = 0) -> "TokenSpan":
        return TokenSpan(f'[{bhead}, {self.head}]')

    def get_rtail(self, btail: int = -1) -> "TokenSpan":
        return TokenSpan(f'[{self.tail}, {btail}]')

    def less(self, span: "TokenSpan") -> bool:
        if self.head < span.head:
            return True
        elif self.head > span.head:
            return False
        elif self.contains(span):
            return False
        return True


class DatetimeToken:

    def __init__(self, dt_type: DatetimeType, value, date_txt: str, date_span: str, time_txt: str = None,
                 time_span: str = None):
        self.type = dt_type
        self.text = f'{date_txt}'
        self.value = value if value else dt_type.value
        date_span = TokenSpan(date_span)
        if time_span:
            assert time_txt
            self.text += f' {time_txt}'
            time_span = TokenSpan(time_span)
            if date_span.less(time_span):
                self.span = TokenSpan(f'[{date_span.head}, {time_span.tail}]')
            else:
                self.span = TokenSpan(f'[{time_span.head}, {date_span.tail}]')
        else:
            self.span = date_span

    def __str__(self) -> str:
        formatted = {'type': str(self.type), 'text': self.text,
                     'span': str(self.span), 'value': self.value}
        return json.dumps(formatted, ensure_ascii=False, indent=4)

    def __repr__(self) -> str:
        return str(self)


def group_date_time(date_spans: list, time_spans: list) -> dict:
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
        date_time_dict[ds.list] = time_list
    if len(time_spans) != 0:
        if ds_dir[0] != 0:
            for i in range(1, len(date_spans)):
                if ds_dir[i] == 0:
                    ds_dir[i] = ds_dir[i - 1]
                    date_time_dict[date_spans[i]] = date_time_dict[date_spans[i - 1]]
        else:
            for i in range(len(date_spans) - 2, -1, -1):
                if ds_dir[i] == 0:
                    ds_dir[i] = ds_dir[i + 1]
                    date_time_dict[date_spans[i]] = date_time_dict[date_spans[i + 1]]
    return date_time_dict


def det_type(date_txt: str) -> DatetimeType:
    # TODO Regex, pattern ....

    # Searching for crontime:
    cron_rgx = ['ها', 'هر', 'سالانه', 'سالیانه', 'ماهانه', 'ماهیانه', 'روزانه']
    for rgx in cron_rgx:
        if rgx in date_txt:
            return DatetimeType.CRONTIME, None
    duration_end_markers_rgx = 'تا|لغایت|الی'
    x = re.search(f"^.*({duration_end_markers_rgx}).*$", date_txt)
    if x is not None:
        if len(date_txt.split('تا')) > 1:
            start_date = date_txt.split('تا')
        elif len(date_txt.split('لغایت')) > 1:
            start_date = date_txt.split('لغایت')
        else:
            start_date = date_txt.split('الی')
        return DatetimeType.DURATION, start_date
    return DatetimeType.EXACT, None


def evaluate_datetime(datetime_type: DatetimeType, date_txt: str = None, time_txt: str = None):
    # Evaluate the aboslute value of the corresponding date and time
    yesterday_tomorrow_today = ['دیروز', 'روز گذشته', 'روز پیش', 'روز دیگر', 'فردا', 'امروز', 'روز بعد', 'روز آینده']
    years = ['سال پیش', 'سال قبل', 'سال گذشته', 'سال بعد', 'سال آینده']
    months = ['ماه پیش', 'ماه قبل', 'ماه گذشته', 'ماه بعد', 'ماه آینده']
    if time_txt is not None:
        time_parts = time_txt.split(':')
    if date_txt is not None:
        x = re.search("^[0-9]+/[0-9]+/[0-9]+$", date_txt)
    # assert datetime_type == DatetimeType.EXACT
    if date_txt is not None and x is not None:
        date_parts = date_txt.split('/')
        greg_date = jdatetime.JalaliToGregorian(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
        if time_txt is not None:
            greg = datetime.datetime(greg_date.gyear, greg_date.gmonth, greg_date.gday, int(time_parts[0]),
                                     int(time_parts[1]), int(time_parts[2]))
        else:
            greg = datetime.datetime(greg_date.gyear, greg_date.gmonth, greg_date.gday, int(time_parts[0]),
                                     0, 0)
        return int(greg.timestamp())
    elif date_txt is not None:
        if time_txt is None:
            hour, minute, second = 0, 0, 0
        else:
            hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
        for tom_yest_tod in yesterday_tomorrow_today:
            if tom_yest_tod in date_txt:
                if re.search("^[0-9]+.*$", date_txt) is not None:
                    number = int(date_txt.split(' ')[0])
                else:
                    number = 1
                if tom_yest_tod == 'فردا' or tom_yest_tod == 'روز آینده' or tom_yest_tod == 'روز دیگر' or tom_yest_tod == 'روز بعد':
                    sign = 1
                elif tom_yest_tod == 'امروز':
                    sign = 0
                else:
                    sign = -1
                greg = datetime.datetime.now() + sign * datetime.timedelta(days=number)
                if time_txt is not None:
                    greg = greg.replace(hour=hour, minute=minute, second=second)
                else:
                    greg = greg.replace(hour=23, minute=59, second=59)
                return int(greg.timestamp())
        for year_pattern in years:
            if year_pattern in date_txt:
                if re.search("^[0-9]+.*$", date_txt) is not None:
                    number = int(date_txt.split(' ')[0])
                else:
                    number = 1
                if year_pattern == 'سال بعد' or year_pattern == 'سال آینده' or year_pattern == 'سال دیگر':
                    sign = 1
                else:
                    sign = -1
                greg = datetime.datetime.now() + sign * relativedelta.relativedelta(months=12 * number)
                if time_txt is not None:
                    greg = greg.replace(hour=hour, minute=minute, second=second)
                else:
                    greg = greg.replace(hour=23, minute=59, second=59)
                return int(greg.timestamp())
        for month_pattern in months:
            if month_pattern in date_txt:
                if re.search("^[0-9]+.*$", date_txt) is not None:
                    number = int(date_txt.split(' ')[0])
                else:
                    number = 1
                if month_pattern == 'ماه بعد' or month_pattern == 'ماه آینده':
                    sign = 1
                else:
                    sign = -1
                greg = datetime.datetime.now() + sign * relativedelta.relativedelta(months=number)
                if time_txt is not None:
                    greg = greg.replace(hour=hour, minute=minute, second=second)
                else:
                    greg = greg.replace(hour=23, minute=59, second=59)
                return int(greg.timestamp())
        if date_txt == 'پارسال':
            greg = datetime.datetime.now() + relativedelta.relativedelta(months=12)
            if time_txt is not None:
                greg = greg.replace(hour=hour, minute=minute, second=second)
            print(int(greg.timestamp()))
            return int(greg.timestamp())
    else:
        return None



def evaluate_crontime(date_txt: str, time_txt: str = None) -> str:
    # TODO this needs evaluation and improvement, it does not cover many cases
    month_pat = 'ماه'
    monthly = 'ماهانه'
    day_pat = "روز"
    days_pat = "روزها"
    har = "هر"
    va = "و"
    ta = "تا"
    if time_txt is not None:
        cron_stamp = str(int(time_txt.split(':')[0])) + " " + str(int(time_txt.split(':')[1]))
    else:
        cron_stamp = "0 0"
    if re.search(f"^.*{har}[ ]+{month_pat}.*$", date_txt) is not None or re.search(f"^.*{monthly}.*$",
                                                                                   date_txt) is not None:
        # dealing with monthly events
        days = set()
        if re.search(f"^{day_pat}[ ]+[0-9]+.+$", date_txt) is not None:
            days.add(date_txt.split()[1])
            for i in range(len(date_txt.split())):
                if date_txt[i] == va:
                    if date_txt[i - 1].isnumeric():
                        days.add(date_txt[i - 1])
                        days.add(date_txt[i + 1])
        else:
            days.add("1")
        day_numbers = ""
        for day_part in days:
            day_numbers = day_numbers + day_part + ','
        day_numbers = day_numbers[:-1]
        cron_stamp = day_numbers + " " + cron_stamp

        months = []
        for month in persian_months.keys():
            if month in date_txt:
                months.append(month)
        if len(months) > 1:
            month_number = ""
            for month in months:
                month_number = month_number + str(persian_months[month]) + ','
            month_number = month_number[:-1]
        elif len(months) == 1:
            month_number = str(persian_months[months[0]])
        else:
            month_number = "*"
        cron_stamp = month_number + " " + cron_stamp
        week_days = []
        if re.search(f"^.*{va}.*$", date_txt) is not None:
            parts = date_txt.split()
            for i in range(len(parts)):
                if parts[i] == va:
                    if parts[i - 1] in persian_days.keys():
                        week_days.append(parts[i - 1])
                        week_days.append(parts[i + 1])
        else:
            for weekday in date_txt.split():
                if weekday in persian_days.keys():
                    week_days.append(weekday)
        if len(week_days) > 1:
            week_number = ""
            for weekday in week_days:
                week_number = week_number + str(persian_days[weekday][1]) + ','
            week_number = week_number[:-1]
        elif len(week_days) == 1:
            week_number = str(persian_days[week_days[0]][1])
        else:
            week_number = "*"
        cron_stamp = week_number + " " + cron_stamp
        print(cron_stamp)
        return cron_stamp
    elif re.search(f"^.*{har}.*{day_pat}.*$", date_txt) is not None:
        if re.search(f"^.*{har}[ ]+[0-9۱۲۳۴۵۶۷۸۹۰]+[ ]+{day_pat}.*$", date_txt) is not None:
            for i in range(len(date_txt.split())):
                if unidecode(date_txt.split()[i]).isnumeric():
                    if date_txt.split()[i - 1] == har and date_txt.split()[i + 1] == day_pat:
                        cron_stamp = "*/" + unidecode(date_txt.split()[i]) + " " + cron_stamp
        else:
            cron_stamp = "* " + cron_stamp
        months = []
        for month in persian_months.keys():
            if month in date_txt:
                months.append(month)
        if len(months) > 1:
            month_number = ""
            for month in months:
                month_number = month_number + str(persian_months[month]) + ','
            month_number = month_number[:-1]
        elif len(months) == 1:
            month_number = str(persian_months[months[0]])
        else:
            month_number = "*"
        cron_stamp = month_number + " " + cron_stamp
        # i can't think of examples with weekdays involved so i assume * for it
        cron_stamp = "* " + cron_stamp

        print(cron_stamp)
        return cron_stamp
    elif re.search(f"^.*{har}[ ]+.*شنبه.*$", date_txt) is not None or re.search(f"^.*{har}[ ]+جمعه.*$",
                                                                                date_txt) is not None:
        cron_stamp = "* * " + cron_stamp
        week_days = []
        if re.search(f"^.*{va}.*$", date_txt) is not None:
            parts = date_txt.split()
            for i in range(len(parts)):
                if parts[i] == va:
                    if parts[i - 1] in persian_days.keys():
                        week_days.append(parts[i - 1])
                        week_days.append(parts[i + 1])
        else:
            for weekday in date_txt.split():
                if weekday in persian_days.keys():
                    week_days.append(weekday)
        if len(week_days) > 1:
            week_number = ""
            for weekday in week_days:
                week_number = week_number + str(persian_days[weekday][1]) + ','
            week_number = week_number[:-1]
        elif len(week_days) == 1:
            week_number = str(persian_days[week_days[0]][1])
        else:
            week_number = "*"
        cron_stamp = week_number + " " + cron_stamp
        print(cron_stamp)
        return cron_stamp
    else:
        print("* * * * *")
        return "* * * * *"
