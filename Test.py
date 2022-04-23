from parstdex import Parstdex
model = Parstdex()

sentence_list = ['دیروز درست در ساعت پنج و چهل و یک دقیقه صدای گوش خراشی از چهارراه نزدیک خانه به گوش می‌رسید',
                 'اتفاقات امروز تا دو روز دیگر می‌تواند برای مردم ایران بسیار حساس باشد',
                 'کامران هر روز هفته ساعت دو و سی دقیقه بعدازظهر و چهار و پنجاه دقیقه صبح به مدرسه می‌رود',
                 'قرار است پنج اردیبهشت ۱۴۰۲ جلسه‌ای در رابطه با گرمایش جهانی راس ساعت ۵ عصر برگزار شود',
                 'سه‌شنبه ساعت ۵ عصر جلسه هست',
                 'ساعت چهار و چهل دقیقه بعدازظهر می‌میرم.'
                 ]

for sentence in sentence_list[2:3]:
    markers = model.extract_marker(sentence)

    print(f'***')
    print(markers['datetime'])

    for s in markers['datetime'].keys():
        values = model.extract_value(markers['datetime'][s])
        for key in values.keys():
            print(f'{key}\n{values[key]}')
            print('####')