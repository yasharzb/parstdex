import pprint
import time
from turtle import st

from parstdex.utils.tokenizer import tokenize_words
import textspan

from parstdex.utils.normalizer import Normalizer
from parstdex.utils.pattern_to_regex import Patterns
from parstdex.utils.spans import create_spans
from parstdex.utils.spans import merge_spans
from parstdex.utils.word_to_value import ValueExtractor
from parstdex.utils.deprecation import deprecated

from parstdex.datetime_determination_util import *
from typing import List


class MarkerExtractor(object):
    def __init__(self, debug_mode=False):
        # Normalizer: convert arabic YE and KAF to persian ones.
        self.normalizer = Normalizer()
        # Patterns: patterns to regex generator
        self.regexes = Patterns.getInstance().regexes
        # ValueExtractor: value extractor from known time and date
        self.value_extractor = ValueExtractor()
        self.DEBUG = debug_mode
        self.extract_span("")
        super(MarkerExtractor, self).__init__()

    def extract_span(self, input_sentence: str):
        """
        function should output list of spans, each item in list is a time marker span present in the input sentence.
        :param input_sentence: input sentence
        :return:
        markers: all extracted spans
        """

        # apply normalizer on input sentence
        normalized_sentence = self.normalizer.normalize_cumulative(
            input_sentence)

        # Create spans
        output_raw, spans = create_spans(self.regexes, normalized_sentence)

        if self.DEBUG:
            # Print raw output
            dict_output_raw = {}
            for key in output_raw.keys():
                dict_output_raw[key] = []
                for match in output_raw[key]:
                    start = match.regs[0][0]
                    end = match.regs[0][1]
                    dict_output_raw[key].append({
                        "token": match.string[start:end],
                        "span": [start, end]
                    })
            pprint.pprint(dict_output_raw)

        if len(spans['time']) == 0 and len(spans['date']) == 0:
            return {'datetime': [], 'date': [], 'time': []}

        spans = merge_spans(spans, normalized_sentence)

        return spans

    def extract_marker(self, input_sentence: str):
        markers = {'datetime': {}, 'date': {}, 'time': {}}

        spans = self.extract_span(input_sentence)
        for key in spans.keys():
            spans_list = spans[key]
            markers[key] = {str(span): input_sentence[span[0]: span[1]]
                            for span in spans_list}

        return markers

    def extract_value(self, input_sentence: str):
        """
        function should output list of values, each item in list is a time marker value present in the input sentence.
        :param input_sentence: input sentence
        :return:
        normalized_sentence: normalized sentence
        result: all extracted spans
        values: all extracted time-date values
        """

        values = {"time": {}, "date": {}}
        spans = self.extract_span(input_sentence)

        time_spans = spans['time']
        date_spans = spans['date']

        time_values = [self.value_extractor.compute_time_value(
            input_sentence[e[0]:e[1]]) for e in time_spans]
        date_values = [self.value_extractor.compute_date_value(
            input_sentence[e[0]:e[1]]) for e in date_spans]

        values['time'] = {str(span): str(value)
                          for span, value in zip(time_spans, time_values)}
        values['date'] = {str(span): str(value)
                          for span, value in zip(date_spans, date_values)}

        return values

    @deprecated("extract_ner will be deprecated soon. Use extract_bio_dat or extract_bio_dattim instead.")
    def extract_ner(self, input_sentence: str, tokenizer=None):
        return self.extract_bio_dat(input_sentence, tokenizer)

    def extract_bio_dat(self, input_sentence: str, tokenizer=None):
        """
        You can pass any custom tokenizer to tokenize sentences.
        :param input_sentence:
        :param tokenizer:
        :return:
        """
        spans_dict = self.extract_span(input_sentence)
        spans = spans_dict['datetime']
        ners = []
        tokens = tokenize_words(input_sentence) if not tokenizer else tokenizer
        all_spans = textspan.get_original_spans(tokens, input_sentence)
        all_spans = [span[0] for span in all_spans if span != []]
        for span in all_spans:
            chosen = False
            for ner_span in spans:
                if span[0] >= ner_span[0] and span[1] <= ner_span[1]:
                    if span[0] == ner_span[0]:
                        ners.append((input_sentence[span[0]:span[1]], 'B-DAT'))
                    else:
                        ners.append((input_sentence[span[0]:span[1]], 'I-DAT'))
                    chosen = True
                    break
            if not chosen:
                ners.append((input_sentence[span[0]:span[1]], 'O'))
        return ners

    def extract_bio_dattim(self, input_sentence: str, tokenizer=None):
        """
        You can pass any custom tokenizer to tokenize sentences.
        :param input_sentence:
        :param tokenizer:
        :return:
        """
        spans_dict = self.extract_span(input_sentence)
        time_spans = spans_dict['time']
        date_spans = spans_dict['date']
        spans = time_spans + date_spans
        ners = []
        tokens = tokenize_words(input_sentence) if not tokenizer else tokenizer
        all_spans = textspan.get_original_spans(tokens, input_sentence)
        all_spans = [span[0] for span in all_spans if span != []]
        for span in all_spans:
            chosen = False
            for ner_span in spans:
                if span[0] >= ner_span[0] and span[1] <= ner_span[1]:
                    if span[0] == ner_span[0]:
                        if ner_span in time_spans:
                            ners.append(
                                (input_sentence[span[0]:span[1]], 'B-TIM'))
                        elif ner_span in date_spans:
                            ners.append(
                                (input_sentence[span[0]:span[1]], 'B-DAT'))
                    else:
                        if ner_span in time_spans:
                            ners.append(
                                (input_sentence[span[0]:span[1]], 'I-TIM'))
                        elif ner_span in date_spans:
                            ners.append(
                                (input_sentence[span[0]:span[1]], 'I-DAT'))
                    chosen = True
                    break
            if not chosen:
                ners.append((input_sentence[span[0]:span[1]], 'O'))
        return ners

    def extract_datetime_tokens(self, input_sentence: str) -> list:
        values = self.extract_value(input_sentence)
        markers = self.extract_marker(input_sentence)
        tokens = []
        date_spans = list(markers['date'].keys())
        time_spans = list(values['time'].keys())
        datetime_dict = group_date_time(date_spans, time_spans)
        date_token_types = {}
        duration_tokens = {}
        for date in date_spans:
            token_type, split_durations = det_type(values['date'][date])
            if split_durations:
                assert token_type == DatetimeType.DURATION and len(split_durations) == 2
                start_date_txt, end_date_txt = split_durations[0], split_durations[1]
                duration_tokens[date] = [end_date_txt, evaluate_datetime(token_type, start_date_txt)]
            date_token_types[date] = token_type
        for date in date_spans:
            token_type = date_token_types[date]
            if len(datetime_dict[date]) == 0:
                token = _handle_semi_determined_tokens(token_type, duration_tokens, markers, values, date)
                tokens.append(token)
            else:
                for time_k in datetime_dict[date]:
                    token = _handle_semi_determined_tokens(token_type, duration_tokens, markers, values, date,
                                                           time_k=time_k)
                    tokens.append(token)
        return tokens


def _handle_semi_determined_tokens(token_type: DatetimeType, duration_tokens: dict, markers: dict, values: dict,
                                   date: str, time_k: str = None):
    date_numeric_txt, date_txt = values['date'][date], markers['date'][date]
    time_numeric_txt = values['time'][time_k] if time_k else None
    time_txt = markers['time'][time_k] if time_k else None
    token: DatetimeToken
    if token_type == DatetimeType.CRONTIME:
        dt_value = evaluate_crontime(date_numeric_txt, time_numeric_txt)
        token = DatetimeToken(token_type, dt_value, date_txt, date, time_txt, time_k)
    elif token_type == DatetimeType.EXACT:
        dt_value = evaluate_datetime(token_type, date_numeric_txt, time_numeric_txt)
        token = DatetimeToken(token_type, dt_value, date_txt, date, time_txt, time_k)
    else:
        assert token_type == DatetimeType.DURATION
        date_numeric_txt, prev_timestamp = duration_tokens[date][0], duration_tokens[date][1]
        dt_value = evaluate_datetime(token_type, date_numeric_txt, time_numeric_txt)
        token = DatetimeToken(token_type, [prev_timestamp, dt_value], date_txt, date, time_txt, time_k)
    return token
