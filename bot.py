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


SERVICES = {
    "manicure": {
        "title": "💅 Маникюр",
        "image": "manicure_card.png",
        "text": "💅 <b>Маникюр</b>\n\nКрасивые и ухоженные руки каждый день.\n\n• классический маникюр\n• маникюр + гель-лак\n• укрепление ногтей\n• дизайн ногтей\n\nСтоимость: <b>от 80 zł</b>",
    },
    "pedicure": {
        "title": "👣 Педикюр",
        "image": "pedicure_card.png",
        "text": "👣 <b>Педикюр</b>\n\nКомфорт, легкость и аккуратный результат.\n\n• классический педикюр\n• педикюр + гель-лак\n• аппаратный педикюр\n• SPA-педикюр\n\nСтоимость: <b>от 100 zł</b>",
    },
    "hair": {
        "title": "💇‍♀️ Волосы",
        "image": "hair_card.png",
        "text": "💇‍♀️ <b>Парикмахерские услуги</b>\n\nПрофессиональный уход и стиль для ваших волос.\n\n• женская стрижка\n• укладка\n• окрашивание\n• мелирование / балаяж\n• тонирование\n\nСтоимость: <b>от 100 zł</b>",
    },
    "brows": {
        "title": "👁 Брови и ресницы",
        "image": "brows_lashes_card.png",
        "text": "👁 <b>Брови и ресницы</b>\n\nВыразительный взгляд и аккуратная форма.\n\n• коррекция бровей\n• окрашивание бровей\n• ламинирование ресниц\n• окрашивание ресниц\n\nСтоимость: <b>от 50 zł</b>",
    },
    "cosmetology": {
        "title": "💆 Косметология",
        "image": "cosmetology_card.png",
        "text": "💆 <b>Косметология</b>\n\nПрофессиональный уход для чистой и сияющей кожи.\n\n• чистка лица\n• пилинг\n• уход по типу кожи\n• мезотерапия\n\nСтоимость: <b>от 150 zł</b>",
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
    if not path.exists():
        path = BASE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {filename}")
    return FSInputFile(path)


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
    for name in ["Анна", "Мария", "Екатерина"]:
        kb.button(text=name, callback_data=f"select_master:{name}")
    kb.adjust(1)
    return kb.as_markup()


def kb_dates():
    kb = InlineKeyboardBuilder()
    for d in ["Сегодня", "Завтра", "На этой неделе"]:
        kb.button(text=d, callback_data=f"select_date:{d}")
    kb.adjust(1)
    return kb.as_markup()


def kb_times():
    kb = InlineKeyboardBuilder()
    for t in ["10:00", "12:00", "14:00", "16:00", "18:00"]:
        kb.button(text=t, callback_data=f"select_time:{t}")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


async def send_card(target, image: str, text: str, markup=None):
    if isinstance(target, CallbackQuery):
        await target.message.answer_photo(pic(image), caption=text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer_photo(pic(image), caption=text, reply_markup=markup)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await send_card(message, "welcome_banner.png", "👋 <b>Добро пожаловать в ES Beauty Bar</b>\n\nПремиальный салон красоты в Варшаве.\nВыберите раздел ниже:", kb_main())


@dp.callback_query(F.data == "menu")
async def menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_card(call, "welcome_banner.png", "🏠 <b>Главное меню</b>\n\nВыберите нужный раздел:", kb_main())


@dp.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    await send_card(call, "about_card.png", "🏛 <b>О салоне</b>\n\nES Beauty Bar — место, где красота, комфорт и профессиональный уход соединяются в одном пространстве.", kb_about())


@dp.callback_query(F.data == "advantages")
async def advantages(call: CallbackQuery):
    await send_card(call, "advantages_card.png", "✨ <b>Почему выбирают нас</b>\n\nПремиум-материалы, опытные мастера, стерильность и индивидуальный подход.", kb_back())


@dp.callback_query(F.data == "visit")
async def visit(call: CallbackQuery):
    await send_card(call, "care_card.png", "🤍 <b>Как проходит визит</b>\n\nЗапись → консультация → процедура → результат → рекомендации по уходу.", kb_back())


@dp.callback_query(F.data == "services")
async def services(call: CallbackQuery):
    await send_card(call, "services_card.png", "💎 <b>Наши услуги</b>\n\nВыберите услугу, чтобы посмотреть подробнее:", kb_services())


@dp.callback_query(F.data.startswith("service:"))
async def service_detail(call: CallbackQuery):
    code = call.data.split(":", 1)[1]
    item = SERVICES[code]
    await send_card(call, item["image"], item["text"], kb_after_service(code))


@dp.callback_query(F.data == "price")
async def price(call: CallbackQuery):
    await send_card(call, "price_card.png", "💵 <b>Прайс</b>\n\n💅 Маникюр — от <b>80 zł</b>\n👣 Педикюр — от <b>100 zł</b>\n💇‍♀️ Волосы — от <b>100 zł</b>\n👁 Брови и ресницы — от <b>50 zł</b>\n💆 Косметология — от <b>150 zł</b>", kb_back())


@dp.callback_query(F.data == "masters")
async def masters(call: CallbackQuery):
    await send_card(call, "masters_card.png", "👩‍🎨 <b>Наши мастера</b>\n\nОпытные специалисты, которые подберут идеальное решение для вас.", kb_back())


@dp.callback_query(F.data == "promo")
async def promo(call: CallbackQuery):
    await send_card(call, "promo_card.png", "🎁 <b>Акции</b>\n\n• -10% на первое посещение\n• -15% в день рождения\n• бонусы постоянным клиентам", kb_back())


@dp.callback_query(F.data == "reviews")
async def reviews(call: CallbackQuery):
    await send_card(call, "reviews_card.png", "⭐ <b>Отзывы клиентов</b>\n\nНам доверяют за качество, уютную атмосферу и внимательное отношение.", kb_back())


@dp.callback_query(F.data == "contacts")
async def contacts(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗺 Как нас найти", callback_data="map")
    kb.button(text="📅 Записаться", callback_data="booking")
    kb.button(text="⬅️ Главное меню", callback_data="menu")
    kb.adjust(1)
    await send_card(call, "contacts_card.png", "📞 <b>Контакты</b>\n\nАдрес: ul. Nowy Świat 45/2, Warszawa\nТелефон: +48 123 456 789\nTelegram: @es_beauty_bar\nInstagram: @es_beauty_bar", kb.as_markup())


@dp.callback_query(F.data == "map")
async def map_card(call: CallbackQuery):
    await send_card(call, "map_card.png", "🗺 <b>Как нас найти</b>\n\nМы находимся в центре Варшавы. Удобно добраться пешком, на метро или авто.", kb_back())


@dp.callback_query(F.data == "faq")
async def faq(call: CallbackQuery):
    await send_card(call, "faq_card.png", "❓ <b>Вопросы и ответы</b>\n\nЗдесь собраны ответы на частые вопросы: запись, оплата, отмена визита, акции и контакты.", kb_back())


@dp.callback_query(F.data == "booking")
async def booking(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await send_card(call, "booking_card.png", "📅 <b>Онлайн-запись</b>\n\nВыберите услугу:", kb_booking_services())
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
    await state.update_data(master=call.data.split(":", 1)[1])
    await call.message.answer("📅 Выберите дату:", reply_markup=kb_dates())
    await state.set_state(Booking.date)
    await call.answer()


@dp.callback_query(F.data.startswith("select_date:"))
async def select_date(call: CallbackQuery, state: FSMContext):
    await state.update_data(date=call.data.split(":", 1)[1])
    await call.message.answer("⏰ Выберите время:", reply_markup=kb_times())
    await state.set_state(Booking.time)
    await call.answer()


@dp.callback_query(F.data.startswith("select_time:"))
async def select_time(call: CallbackQuery, state: FSMContext):
    await state.update_data(time=call.data.split(":", 1)[1])
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
    admin_text = (
        "📩 <b>Новая запись в ES Beauty Bar</b>\n\n"
        f"💎 Услуга: {data.get('service')}\n"
        f"👩‍🎨 Мастер: {data.get('master')}\n"
        f"📅 Дата: {data.get('date')}\n"
        f"⏰ Время: {data.get('time')}\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📱 Контакт: {data.get('phone')}"
    )
    if ADMIN_ID:
        try:
            await bot.send_message(int(ADMIN_ID), admin_text)
        except Exception as e:
            logging.warning("Admin notification failed: %s", e)

    await message.answer_photo(pic("success_card.png"), caption="✅ <b>Спасибо за запись!</b>\n\nМы получили вашу заявку и скоро свяжемся для подтверждения.", reply_markup=kb_main())
    await state.clear()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
