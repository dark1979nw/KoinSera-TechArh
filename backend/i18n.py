from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
import models
import database
from pydantic import BaseModel

class Translation(BaseModel):
    key: str
    translations: dict[str, str]

# Default translations
DEFAULT_TRANSLATIONS = {
    "en": {
        "welcome": "Welcome",
        "login": "Login",
        "register": "Register",
        "logout": "Logout",
        "profile": "Profile",
        "email": "Email",
        "password": "Password",
        "confirm_password": "Confirm Password",
        "first_name": "First Name",
        "last_name": "Last Name",
        "company": "Company",
        "language": "Language",
        "submit": "Submit",
        "cancel": "Cancel",
        "error_invalid_credentials": "Invalid login or password",
        "error_account_locked": "Account is locked for 5 minutes due to too many failed attempts",
        "error_required_field": "This field is required",
        "error_invalid_email": "Invalid email format",
        "error_password_mismatch": "Passwords do not match",
        "error_password_requirements": "Password must be at least 8 characters long and contain letters, numbers, and special characters",
        "success_registration": "Registration successful",
        "success_login": "Login successful",
    },
    "ru": {
        "welcome": "Добро пожаловать",
        "login": "Войти",
        "register": "Зарегистрироваться",
        "logout": "Выйти",
        "profile": "Профиль",
        "email": "Электронная почта",
        "password": "Пароль",
        "confirm_password": "Подтвердите пароль",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "company": "Компания",
        "language": "Язык",
        "submit": "Отправить",
        "cancel": "Отмена",
        "error_invalid_credentials": "Неверный логин или пароль",
        "error_account_locked": "Учетная запись заблокирована на 5 минут из-за превышения количества попыток входа",
        "error_required_field": "Это поле обязательно для заполнения",
        "error_invalid_email": "Неверный формат электронной почты",
        "error_password_mismatch": "Пароли не совпадают",
        "error_password_requirements": "Пароль должен быть не менее 8 символов и содержать буквы, цифры и специальные символы",
        "success_registration": "Регистрация успешна",
        "success_login": "Вход выполнен успешно",
    }
}

def get_user_language(request: Request, db: Session) -> str:
    """
    Determine the user's preferred language based on:
    1. User's language preference in profile (if authenticated)
    2. Accept-Language header
    3. Default to English
    """
    # Try to get language from authenticated user
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from auth import get_current_user
            user = get_current_user(token, db)
            if user and user.language_code:
                return user.language_code
        except:
            pass

    # Try to get language from Accept-Language header
    accept_language = request.headers.get("Accept-Language", "")
    if accept_language:
        # Parse Accept-Language header and get the first language code
        languages = [lang.split(";")[0].strip() for lang in accept_language.split(",")]
        for lang in languages:
            if lang in DEFAULT_TRANSLATIONS:
                return lang

    # Default to English
    return "en"

def get_translation(key: str, language: str) -> str:
    """Get translation for a given key and language"""
    translations = DEFAULT_TRANSLATIONS.get(language, DEFAULT_TRANSLATIONS["en"])
    return translations.get(key, key)

def initialize_languages(db: Session):
    """Initialize default languages in the database"""
    for code, translations in DEFAULT_TRANSLATIONS.items():
        language = db.query(models.Language).filter(models.Language.code == code).first()
        if not language:
            language = models.Language(
                code=code,
                name=translations.get("language", code.upper()),
                is_default=(code == "en")
            )
            db.add(language)
    db.commit() 