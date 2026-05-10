from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetDefinition:
    key: str
    name: str
    url: str
    form_selector: str
    submit_selector: str
    success_indicators: list[str]
    error_indicators: list[str]
    default_valid_data: dict[str, str]
    field_aliases: dict[str, str] = field(default_factory=dict)


TARGETS: dict[str, TargetDefinition] = {
    "parabank_register": TargetDefinition(
        key="parabank_register",
        name="ParaBank Register for Free Online Account Access",
        url="https://parabank.parasoft.com/parabank/register.htm",
        form_selector="form",
        submit_selector="input[value='Register'], input[type='submit']",
        success_indicators=[
            "Your account was created successfully",
            "You are now logged in",
            "Welcome",
        ],
        error_indicators=[
            "is required",
            "Passwords did not match",
            "already exists",
            "Error",
        ],
        default_valid_data={
            "customer.firstName": "John",
            "customer.lastName": "Tester",
            "customer.address.street": "123 QA Street",
            "customer.address.city": "Dhaka",
            "customer.address.state": "Dhaka",
            "customer.address.zipCode": "1207",
            "customer.phoneNumber": "01700000000",
            "customer.ssn": "123456789",
            "customer.username": "qauser_${UNIQUE}",
            "customer.password": "SecurePass123",
            "repeatedPassword": "SecurePass123",
        },
    ),
    "automation_exercise_signup": TargetDefinition(
        key="automation_exercise_signup",
        name="Automation Exercise Signup / Login",
        url="https://www.automationexercise.com/login",
        form_selector="form[action='/signup']",
        submit_selector="form[action='/signup'] button[type='submit'], button[data-qa='signup-button']",
        success_indicators=[
            "ENTER ACCOUNT INFORMATION",
            "New User Signup",
            "Signup",
        ],
        error_indicators=[
            "Email Address already exist",
            "required",
            "Please include an '@'",
            "Please fill out this field",
        ],
        default_valid_data={
            "name": "QA Tester",
            "email": "qa_${UNIQUE}@example.com",
        },
    ),
}


def get_target(target_key: str) -> TargetDefinition:
    try:
        return TARGETS[target_key]
    except KeyError as exc:
        available = ", ".join(TARGETS)
        raise KeyError(f"Unknown target '{target_key}'. Available targets: {available}") from exc
