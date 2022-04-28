from operator import mod
from parstdex import Parstdex
from parstdex.utils.pattern_to_regex import Patterns

model = Parstdex()

sentences = ['دیروز درست در ساعت پنج و چهل و یک دقیقه صدای گوش خراشی از چهارراه نزدیک خانه به گوش می‌رسید',
             'اتفاقات از امروز تا 2 روز دیگر می‌تواند برای مردم ایران بسیار حساس باشد',
             'نمایشگاه از فردا تا 1 ماه بعد برقرار است ',
             'صادق از دیروز تا دو سال آینده در فرانسه زندگی می‌کند',
             'کامران هر روز هفته به مدرسه می‌رود',
             'نخستین بازی‌های گروه ایران در جام‌جهانی سی آبان ۱۴۰۱ در ساعت ۱ بعدازظهر، ۶ عصر برگزار خواهد شد.',
             'سمیه هر ماه برمی‌گردد',
             'این قرص باید هر 2 روز یکبار مصرف شود',
             'کلاس ورزش هر شنبه و دوشنبه برگزار می‌شود',
             'هر شنبه بهمن ماه شرکت یک مهمانی می‌گیرد'
             ]


def get_tokens(sentence: str):
    tokens = model.extract_datetime_tokens(sentence)
    print(tokens)


for i in range(len(sentences)):
    sentence = sentences[i]
    get_tokens(sentence)
