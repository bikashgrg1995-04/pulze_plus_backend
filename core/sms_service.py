def send_sms(phone_number: str, message: str) -> None:
    """
    Development SMS service.
    No real SMS is sent.
    The message is printed to the Django console.
    """
    print(
        "\n"
        "================ DEVELOPMENT SMS ================\n"
        f"To: {phone_number}\n"
        f"Message: {message}\n"
        "==================================================\n"
    )