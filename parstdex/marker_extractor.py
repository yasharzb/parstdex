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

    def extract_datetime_tokens(self, input_sentence: str):
        values = self.extract_value(input_sentence)
        markers = self.extract_marker(input_sentence)
        tokens = []
        date_spans = list(markers['date'].keys())
        time_spans = list(values['time'].keys())
        datetime_dict = group_date_time(date_spans, time_spans)
        date_token_types = {}
        for date in datetime_dict.keys():
            date_token_types[date] = det_type(markers['date'][date])
        for date in datetime_dict.keys():
            if len(datetime_dict[date]) == 0:
                token = _handle_semi_determined_tokens(date_token_types, markers, values, date)
                tokens.append(token)
            else:
                for time_k in datetime_dict[date]:
                    token = _handle_semi_determined_tokens(date_token_types, markers, values, date, time_k)
                    tokens.append(token)
        tokens_count = len(tokens)
        for i in range(tokens_count):
            token: DatetimeToken = tokens[i]
            if token.type == DatetimeType.DURATION:
                prev_token: DatetimeToken = tokens[i - 1]
                token.value = [prev_token.value, token.value]
                del tokens[i]
                i -= 1
                tokens_count -= 1
        return tokens

    def extract_test(self, input_sentence: str):
        values = self.extract_value(input_sentence)
        date_spans = list(values['date'].keys())
        time_spans = list(values['time'].keys())
        date_time_dict = group_date_time(date_spans, time_spans)
        return date_time_dict, values

    def det_test(self, string: str):
        return det_type(string)

    def eval_date_time_test(self, datetime_type, date: str, time: str):
        evaluate_datetime(datetime_type, date, time)


def _handle_semi_determined_tokens(date_token_types: dict, markers: dict, values: dict, date: str, time_k: str = None):
    token_type = date_token_types[date]
    date_txt = markers['date'][date]
    time_txt = values['time'][time_k] if time_k else None
    token: DatetimeToken
    if token_type == DatetimeType.CRONTIME:
        print(date_txt, time_txt)
        dt_value = evaluate_crontime(date_txt, time_txt)
        token = DatetimeToken(token_type, date_txt, time_txt, date, time_k, dt_value)
    elif token_type == DatetimeType.EXACT:
        dt_value = evaluate_datetime(token_type, date_txt, time_txt)
        token = DatetimeToken(token_type, date_txt, time_txt, date, time_k, dt_value)
    else:
        token = None
    return token
