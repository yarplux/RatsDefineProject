
TIME_AREA = [104, 0, 155, 12, 212, 50]

FILE_OPTIONS_FOLDER = './general_options.txt'
FILE_OPTIONS_DEFAULT = './options.txt'

DIALOG_TITLE_OPEN_VIDEO = 'Выберете файл видео'
DIALOG_TITLE_GENERAL = 'Обработка'
DIALOG_TITLE_WARNING = 'Уведомление'

DIALOG_TEXT_ERROR_OPEN_FILE = 'Для работа необходимо выбрать файл!'
DIALOG_TEXT_WARNING_TIME_AREA = 'Выберете область расположения времени в кадре'
DIALOG_TEXT_WARNING_TIME = 'Введите корректное время (формат: ЧАСЫ МИНУТЫ СЕКУНДЫ)'
DIALOG_TEXT_WARNING_ACTION = 'Выберете фиксируемое движение'

DIALOG_TEXT_EXIT = 'Вы действительно хотите выйти?'
DIALOG_TEXT_ANOTHER = 'Вы хотите выбрать другой файл?'

DIALOG_TEXT_SAVE_TRACK = 'Cохранить текущий трек?'
DIALOG_TEXT_SAVE_OPTIONS = 'Cохранить текущие настройки обработки видео?'
DIALOG_TEXT_SAVE_GENERAL = 'Cохранить текущие общие настройки ( + текущий список движений)?'
DIALOG_TEXT_SAVE_OPTIONS_DEFAULT = 'Сохранить как настройки обработки по-умолчанию?'

DIR_OPTIONS = './options'
DIR_TRACKS = './tracks'
DIR_RESULTS = './results'

INSTRUCTIONS = 'Для начала:\n' + \
 ' - Установите стартовую позицию траектории мышкой на видео \n' + \
 ' - Все необходимые параметры в панели настроек \n' + \
 ' - Нажмите любую клавишу \n' + \
 'В процессе работы: \n' + \
 'Для выхода нажмите ESC, для паузы пробел \n' + \
 'При подозрении на ошибку распознавания - видео само ставится на паузу \n' + \
 '(для продолжения отрегулируйте фильтры и снимите с паузы пробелом) \n' + \
 'В режиме паузы: \n' +\
'Стрелка вправо на клавиатуре - перемотка вперёд со скоростью движка FrameDelta' + \
'Стрелка влево на клавиатуре - перемотка назад со скоростью движка FrameDelta'