from operator import mod
from parstdex import Parstdex
from parstdex.utils.pattern_to_regex import Patterns

model = Parstdex()

sentence_list = ['دیروز درست در ساعت پنج و چهل و یک دقیقه صدای گوش خراشی از چهارراه نزدیک خانه به گوش می‌رسید',
                 'اتفاقات امروز تا دو روز دیگر می‌تواند برای مردم ایران بسیار حساس باشد',
                 'کامران هر روز هفته ساعت دو و سی دقیقه بعدازظهر و چهار و پنجاه دقیقه صبح به مدرسه می‌رود',
                 'قرار است فردا پنج اردیبهشت ۱۴۰۲ جلسه‌ای در رابطه با گرمایش جهانی راس ساعت ۵ عصر برگزار شود',
                 'قرار است امروز جلسه‌ای در رابطه با گرمایش جهانی راس ساعت ۵ عصر برگزار شود',
                 'قرار بود دیروز جلسه‌ای در رابطه با گرمایش جهانی راس ساعت ۵ عصر برگزار شود',
                 'دو ماه گذشته رفتیم سفر',
                 'پنج خرداد ساعت ۳ رفتیم بیرون',
                 'امروز ساعت ۵  به خانه برمی‌گردیم',
                 'فردا ساعت ۲ بعد از ظهر هوا خوب است',
                 'دو ماه قبل پنج خرداد از زندان آزاد شد',
                 'هر دو ماه یکبار ساعت ۵ عصر پیاده روی می‌کند',
                 'هر روز بین دوشنبه تا جمعه ساعت ۱۲ بامداد',
                 'من ۳شنبه و همچنین روز ۴شنبه چهار و چهل دقیقه بعدازظهر کلاس دارم',
                 'یاشار از امروز ساعت ۹ شب تا دوشنبه ساعت ۷ عصر در حال فتح آتن است',
                 'من ساعت ۷ عصر ۳شنبه و همچنین ۴شنبه و همچنین روز ۵شنبه ساعت ۱۲ ظهر کلاس دارم',
                 'من شنبه ساعت ۷ عصر و همچنین ساعت ۸ صبح و ساعت ۲ بعدازهظر چهارشنبه درگیر فتح قسطنطنیه هستم',
                 'از فردا ساعت ۵ تا جمعه ساعت ۶ انتخابات در جریان است',
                 'من ۳شنبه ساعت ۵ و همچنین ۴شنبه ساعت ۷ به مدرسه می‌روم',
                 'ساعت ۴ و  ساعت ۵ و سی روز ۴شنبه خورشیدگرفتگی پیش رو است',
                 'من ساعت ۴ بعد از ظهر روزهای سه‌شنبه ، چهارشنبه و همچنین پنجشنبه کلاس دارم'
                 ]


# for sentence in sentence_list[12:13]:
#     datetime_dict, values = model.extract_test(sentence)
#     print(datetime_dict)
#     for key in values:
#         print(f'=={key}==')
#         print(values[key])
#         for value in values[key].values():
#             print(value)
#             print(model.det_test(value))
#             print()
#     # Currently only supports when time and date dictionaries match in size and correspond to each other
#     #for (k1, v1), (k2, v2) in zip(values['date'].items(), values['time'].items()):
#     #    model.eval_date_time_test(model.det_test(v2), v1, v2)
#     print('\n###\n')
# # pat = Patterns.getInstance()
# # print(pat.cumulative_annotations_keys)

def get_tokens(sentence: str):
    tokens = model.extract_datetime_tokens(sentence)
    print(tokens)


get_tokens('هر سه‌شنبه و جمعه صدای گوش خراشی به گوش می‌رسید')
