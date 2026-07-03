import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

BASE_DIR = Path(__file__).parent
MEDIA_DIR = BASE_DIR / "media"

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add BOT_TOKEN to GitHub Secrets.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# DEMO-база подтвержденных записей.
# Важно: на GitHub Actions хранится только во время текущего запуска.
CONFIRMED_SLOTS = set()
PENDING_BOOKINGS = {}
ALL_TIMES = ["10:00", "12:00", "14:00", "16:00", "18:00"]


def slot_key(master: str, date: str, time: str) -> str:
    return f"{master}|{date}|{time}"


def is_slot_busy(master: str, date: str, time: str) -> bool:
    return slot_key(master, date, time) in CONFIRMED_SLOTS


def get_free_times(master: str, date: str) -> list[str]:
    return [t for t in ALL_TIMES if not is_slot_busy(master, date, t)]


SERVICES = {
    "manicure": {
        "title": "💅 Маникюр",
        "image": "manicure_card.png",
        "text": (
            "💅 <b>Маникюр</b>\n\n"
            "Красивые и ухоженные руки каждый день.\n\n"
            "• классический маникюр\n"
            "• маникюр + гель-лак\n"
            "• укрепление ногтей\n"
            "• дизайн ногтей\n\n"
            "Стоимость: <b>от 80 zł</b>"
        ),
    },
    "pedicure": {
        "title": "👣 Педикюр",
        "image": "pedicure_card.png",
        "text": (
            "👣 <b>Педикюр</b>\n\n"
            "Комфорт, легкость и аккуратный результат.\n\n"
            "• классический педикюр\n"
            "• педикюр + гель-лак\n"
            "• аппаратный педикюр\n"
            "• SPA-педикюр\n\n"
            "Стоимость: <b>от 100 zł</b>"
        ),
    },
    "hair": {
        "title": "💇‍♀️ Волосы",
        "image": "hair_card.png",
        "text": (
            "💇‍♀️ <b>Парикмахерские услуги</b>\n\n"
            "Профессиональный уход и стиль для ваших волос.\n\n"
            "• женская стрижка\n"
            "• укладка\n"
            "• окрашивание\n"
            "• мелирование / балаяж\n"
            "• тонирование\n\n"
            "Стоимость: <b>от 100 zł</b>"
        ),
    },
    "brows": {
        "title": "👁 Брови и ресницы",
        "image": "brows_lashes_card.png",
        "text": (
            "👁 <b>Брови и ресницы</b>\n\n"
            "Выразительный взгляд и аккуратная форма.\n\n"
            "• коррекция бровей\n"
            "• окрашивание бровей\n"
            "• ламинирование ресниц\n"
            "• окрашивание ресниц\n\n"
            "Стоимость: <b>от 50 zł</b>"
        ),
    },
    "cosmetology": {
        "title": "💆 Косметология",
        "image": "cosmetology_card.png",
        "text": (
            "💆 <b>Косметология</b>\n\n"
            "Профессиональный уход для чистой и сияющей кожи.\n\n"
            "• чистка лица\n"
            "• пилинг\n"
            "• уход по типу кожи\n"
            "• мезотерапия\n\n"
            "Стоимость: <b>от 150 zł</b>"
        ),
    },
}


class Booking(StatesGroup):
    service = State()
    master = State()
    date = State()
    time = State()
    name = State()
    phone = State()


def pic(filename: str) -> FSInputFile:
    path = MEDIA_DIR / filename

    if path.exists():
        return FSInputFile(path)

    # Если папки media нет, берем файл из корня репозитория
    return FSInputFile(BASE_DIR / filename)


def kb_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏛 О салоне", callback_data="about")
    kb.button(text="💎 Услуги", callback_data="services")
    kb.button(text="💵 Прайс", callback_data="price")
    kb.button(text="👩‍🎨 Мастера", callback_data="masters")
    kb.button(text="📅 Онлайн-запись", callback_data="booking")
    kb.button(text="🎁 Акции", callback_data="promo")
    kb.button(text="⭐ Отзывы", callback_data="reviews")
    kb.button(text="📞 Контакты", callback_data="contacts")
    kb.button(text="❓ Вопросы", callback_data="faq")
    kb.adjust(2, 2, 1, 2, 2)
    return kb.as_markup()


def kb_back():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    return kb.as_markup()


def kb_about():
    kb = InlineKeyboardBuilder()
    kb.button(text="✨ Почему выбирают нас", callback_data="advantages")
    kb.button(text="🤍 Как проходит визит", callback_data="visit")
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def kb_services():
    kb = InlineKeyboardBuilder()
    kb.button(text="💅 Маникюр", callback_data="service:manicure")
    kb.button(text="👣 Педикюр", callback_data="service:pedicure")
    kb.button(text="💇‍♀️ Волосы", callback_data="service:hair")
    kb.button(text="👁 Брови и ресницы", callback_data="service:brows")
    kb.button(text="💆 Косметология", callback_data="service:cosmetology")
    kb.button(text="📅 Записаться", callback_data="booking")
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def kb_after_service(code: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Записаться на услугу", callback_data=f"book_service:{code}")
    kb.button(text="💵 Смотреть прайс", callback_data="price")
    kb.button(text="⬅️ Все услуги", callback_data="services")
    kb.adjust(1)
    return kb.as_markup()


def kb_booking_services():
    kb = InlineKeyboardBuilder()
    for code, item in SERVICES.items():
        kb.button(text=item["title"], callback_data=f"select_service:{code}")
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def kb_masters():
    kb = InlineKeyboardBuilder()
    kb.button(text="Анна", callback_data="select_master:Анна")
    kb.button(text="Мария", callback_data="select_master:Мария")
    kb.button(text="Екатерина", callback_data="select_master:Екатерина")
    kb.adjust(1)
    return kb.as_markup()


def kb_dates():
    kb = InlineKeyboardBuilder()
    kb.button(text="Сегодня", callback_data="select_date:Сегодня")
    kb.button(text="Завтра", callback_data="select_date:Завтра")
    kb.button(text="На этой неделе", callback_data="select_date:На этой неделе")
    kb.adjust(1)
    return kb.as_markup()


def kb_times(master: str, date: str):
    kb = InlineKeyboardBuilder()
    free_times = get_free_times(master, date)

    if not free_times:
        kb.button(text="❌ Нет свободных окон", callback_data="no_slots")
    else:
        for t in free_times:
            kb.button(text=t, callback_data=f"select_time:{t}")

    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def kb_admin_confirm(booking_id: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить запись", callback_data=f"admin_confirm:{booking_id}")
    kb.button(text="❌ Отклонить", callback_data=f"admin_decline:{booking_id}")
    kb.adjust(1)
    return kb.as_markup()


async def send_card(message_or_call, image: str, text: str, markup=None):
    if isinstance(message_or_call, CallbackQuery):
        await message_or_call.message.answer_photo(pic(image), caption=text, reply_markup=markup)
        await message_or_call.answer()
    else:
        await message_or_call.answer_photo(pic(image), caption=text, reply_markup=markup)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await send_card(
        message,
        "welcome_banner.png",
        (
            "👋 <b>Добро пожаловать в ES Beauty Bar</b>\n\n"
            "Премиальный салон красоты в Варшаве.\n"
            "Выберите раздел ниже:"
        ),
        kb_main()
    )


@dp.callback_query(F.data == "menu")
async def menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_card(
        call,
        "welcome_banner.png",
        "🏠 <b>Главное меню</b>\n\nВыберите нужный раздел:",
        kb_main()
    )


@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await send_card(
        call,
        "about_card.png",
        (
            "🏛 <b>О салоне</b>\n\n"
            "ES Beauty Bar — место, где красота, комфорт и профессиональный уход соединяются в одном пространстве."
        ),
        kb_about()
    )


@dp.callback_query(F.data == "advantages")
async def advantages(call: CallbackQuery):
    await send_card(
        call,
        "advantages_card.png",
        "✨ <b>Почему выбирают нас</b>\n\nПремиум-материалы, опытные мастера, стерильность и индивидуальный подход.",
        kb_back()
    )


@dp.callback_query(F.data == "visit")
async def visit(call: CallbackQuery):
    await send_card(
        call,
        "care_card.png",
        "🤍 <b>Как проходит визит</b>\n\nЗапись → консультация → процедура → результат → рекомендации по уходу.",
        kb_back()
    )


@dp.callback_query(F.data == "services")
async def services(call: CallbackQuery):
    await send_card(
        call,
        "services_card.png",
        "💎 <b>Наши услуги</b>\n\nВыберите услугу, чтобы посмотреть подробнее:",
        kb_services()
    )


@dp.callback_query(F.data.startswith("service:"))
async def service_detail(call: CallbackQuery):
    code = call.data.split(":", 1)[1]
    item = SERVICES[code]
    await send_card(call, item["image"], item["text"], kb_after_service(code))


@dp.callback_query(F.data == "price")
async def price(call: CallbackQuery):
    await send_card(
        call,
        "price_card.png",
        (
            "💵 <b>Прайс</b>\n\n"
            "💅 Маникюр — от <b>80 zł</b>\n"
            "👣 Педикюр — от <b>100 zł</b>\n"
            "💇‍♀️ Волосы — от <b>100 zł</b>\n"
            "👁 Брови и ресницы — от <b>50 zł</b>\n"
            "💆 Косметология — от <b>150 zł</b>"
        ),
        kb_back()
    )


@dp.callback_query(F.data == "masters")
async def masters(call: CallbackQuery):
    await send_card(
        call,
        "masters_card.png",
        "👩‍🎨 <b>Наши мастера</b>\n\nОпытные специалисты, которые подберут идеальное решение для вас.",
        kb_back()
    )


@dp.callback_query(F.data == "promo")
async def promo(call: CallbackQuery):
    await send_card(
        call,
        "promo_card.png",
        (
            "🎁 <b>Акции</b>\n\n"
            "• -10% на первое посещение\n"
            "• -15% в день рождения\n"
            "• бонусы постоянным клиентам"
        ),
        kb_back()
    )


@dp.callback_query(F.data == "reviews")
async def reviews(call: CallbackQuery):
    await send_card(
        call,
        "reviews_card.png",
        "⭐ <b>Отзывы клиентов</b>\n\nНам доверяют за качество, уютную атмосферу и внимательное отношение.",
        kb_back()
    )


@dp.callback_query(F.data == "contacts")
async def contacts(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗺 Как нас найти", callback_data="map")
    kb.button(text="📅 Записаться", callback_data="booking")
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(1)
    await send_card(
        call,
        "contacts_card.png",
        (
            "📞 <b>Контакты</b>\n\n"
            "Адрес: ul. Nowy Świat 45/2, Warszawa\n"
            "Телефон: +48 123 456 789\n"
            "Telegram: @es_beauty_bar\n"
            "Instagram: @es_beauty_bar"
        ),
        kb.as_markup()
    )


@dp.callback_query(F.data == "map")
async def map_card(call: CallbackQuery):
    await send_card(
        call,
        "map_card.png",
        "🗺 <b>Как нас найти</b>\n\nМы находимся в центре Варшавы. Удобно добраться пешком, на метро или авто.",
        kb_back()
    )


@dp.callback_query(F.data == "faq")
async def faq(call: CallbackQuery):
    await send_card(
        call,
        "faq_card.png",
        (
            "❓ <b>Вопросы и ответы</b>\n\n"
            "Здесь собраны ответы на частые вопросы: запись, оплата, отмена визита, акции и контакты."
        ),
        kb_back()
    )


@dp.callback_query(F.data == "booking")
async def booking(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_card(
        call,
        "booking_card.png",
        "📅 <b>Онлайн-запись</b>\n\nВыберите услугу:",
        kb_booking_services()
    )
    await state.set_state(Booking.service)


@dp.callback_query(F.data.startswith("book_service:"))
async def booking_from_service(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":", 1)[1]
    await state.clear()
    await state.update_data(service=SERVICES[code]["title"])
    await call.message.answer("👩‍🎨 Выберите мастера:", reply_markup=kb_masters())
    await state.set_state(Booking.master)
    await call.answer()


@dp.callback_query(F.data.startswith("select_service:"))
async def select_service(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":", 1)[1]
    await state.update_data(service=SERVICES[code]["title"])
    await call.message.answer("👩‍🎨 Выберите мастера:", reply_markup=kb_masters())
    await state.set_state(Booking.master)
    await call.answer()


@dp.callback_query(F.data.startswith("select_master:"))
async def select_master(call: CallbackQuery, state: FSMContext):
    master = call.data.split(":", 1)[1]
    await state.update_data(master=master)
    await call.message.answer("📅 Выберите дату:", reply_markup=kb_dates())
    await state.set_state(Booking.date)
    await call.answer()


@dp.callback_query(F.data.startswith("select_date:"))
async def select_date(call: CallbackQuery, state: FSMContext):
    date = call.data.split(":", 1)[1]
    await state.update_data(date=date)

    data = await state.get_data()
    master = data.get("master")

    if not get_free_times(master, date):
        await call.message.answer(
            "❌ На эту дату нет свободных окон. Выберите другую дату:",
            reply_markup=kb_dates()
        )
    else:
        await call.message.answer(
            "⏰ Выберите свободное время:",
            reply_markup=kb_times(master, date)
        )

    await state.set_state(Booking.time)
    await call.answer()


@dp.callback_query(F.data == "no_slots")
async def no_slots(call: CallbackQuery):
    await call.answer("На эту дату нет свободных окон. Выберите другую дату.", show_alert=True)


@dp.callback_query(F.data.startswith("select_time:"))
async def select_time(call: CallbackQuery, state: FSMContext):
    time = call.data.split(":", 1)[1]
    data = await state.get_data()
    master = data.get("master")
    date = data.get("date")

    if is_slot_busy(master, date, time):
        await call.answer("Это время уже занято. Выберите другое.", show_alert=True)
        await call.message.answer(
            "⏰ Актуальные свободные окна:",
            reply_markup=kb_times(master, date)
        )
        return

    await state.update_data(time=time)
    await call.message.answer("Напишите ваше имя:")
    await state.set_state(Booking.name)
    await call.answer()


@dp.message(Booking.name)
async def booking_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Напишите ваш телефон или Telegram для связи:")
    await state.set_state(Booking.phone)


@dp.message(Booking.phone)
async def booking_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()

    master = data.get("master")
    date = data.get("date")
    time = data.get("time")

    if is_slot_busy(master, date, time):
        await message.answer(
            "❌ Это время уже занято. Пожалуйста, начните запись заново и выберите другое окно.",
            reply_markup=kb_main()
        )
        await state.clear()
        return

    booking_id = f"{message.from_user.id}_{len(PENDING_BOOKINGS) + 1}"
    PENDING_BOOKINGS[booking_id] = {
        "user_id": message.from_user.id,
        "service": data.get("service"),
        "master": master,
        "date": date,
        "time": time,
        "name": data.get("name"),
        "phone": data.get("phone"),
    }

    admin_text = (
        "📩 <b>Новая заявка на запись</b>\n\n"
        f"💎 Услуга: {data.get('service')}\n"
        f"👩‍🎨 Мастер: {master}\n"
        f"📅 Дата: {date}\n"
        f"⏰ Время: {time}\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📱 Контакт: {data.get('phone')}\n\n"
        "Подтвердить запись?"
    )

    if ADMIN_ID:
        try:
            await bot.send_message(
                int(ADMIN_ID),
                admin_text,
                reply_markup=kb_admin_confirm(booking_id)
            )
        except Exception as e:
            logging.warning("Admin notification failed: %s", e)

    await message.answer_photo(
        pic("success_card.png"),
        caption=(
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Администратор проверит окно и подтвердит вашу запись."
        ),
        reply_markup=kb_main()
    )
    await state.clear()


@dp.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm(call: CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID):
        await call.answer("Нет доступа", show_alert=True)
        return

    booking_id = call.data.replace("admin_confirm:", "")
    booking = PENDING_BOOKINGS.get(booking_id)

    if not booking:
        await call.answer("Заявка уже не найдена", show_alert=True)
        return

    key = slot_key(booking["master"], booking["date"], booking["time"])

    if key in CONFIRMED_SLOTS:
        await call.answer("Это окно уже занято", show_alert=True)
        return

    CONFIRMED_SLOTS.add(key)

    try:
        await bot.send_message(
            booking["user_id"],
            (
                "✅ <b>Ваша запись подтверждена!</b>\n\n"
                f"💎 Услуга: {booking['service']}\n"
                f"👩‍🎨 Мастер: {booking['master']}\n"
                f"📅 Дата: {booking['date']}\n"
                f"⏰ Время: {booking['time']}\n\n"
                "До встречи в ES Beauty Bar 🤍"
            )
        )
    except Exception as e:
        logging.warning("Client notification failed: %s", e)

    PENDING_BOOKINGS.pop(booking_id, None)

    await call.message.edit_text(
        call.message.html_text + "\n\n✅ <b>Запись подтверждена. Окно теперь занято.</b>",
        reply_markup=None
    )
    await call.answer("Запись подтверждена")


@dp.callback_query(F.data.startswith("admin_decline:"))
async def admin_decline(call: CallbackQuery):
    if str(call.from_user.id) != str(ADMIN_ID):
        await call.answer("Нет доступа", show_alert=True)
        return

    booking_id = call.data.replace("admin_decline:", "")
    booking = PENDING_BOOKINGS.pop(booking_id, None)

    if booking:
        try:
            await bot.send_message(
                booking["user_id"],
                "❌ <b>К сожалению, выбранное время недоступно.</b>\n\nПожалуйста, выберите другое окно для записи."
            )
        except Exception as e:
            logging.warning("Client decline notification failed: %s", e)

    await call.message.edit_text(
        call.message.html_text + "\n\n❌ <b>Заявка отклонена.</b>",
        reply_markup=None
    )
    await call.answer("Заявка отклонена")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
