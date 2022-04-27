from operator import mod
from parstdex import Parstdex
from parstdex.utils.pattern_to_regex import Patterns

model = Parstdex()

sentences = ['دیروز درست در ساعت پنج و چهل و یک دقیقه صدای گوش خراشی از چهارراه نزدیک خانه به گوش می‌رسید',
             'اتفاقات از امروز تا 2 روز دیگر می‌تواند برای مردم ایران بسیار حساس باشد',
             'کامران هر روز هفته به مدرسه می‌رود',
             'نخستین بازی‌های گروه ایران در جام‌جهانی سی آبان ۱۴۰۱ در ساعت ۱ بعدازظهر، ۶ عصر برگزار خواهد شد.',
             ]


def get_tokens(sentence: str):
    tokens = model.extract_datetime_tokens(sentence)
    print(tokens)


for i in range(len(sentences)):
    sentence = sentences[i]
    get_tokens(sentence)
