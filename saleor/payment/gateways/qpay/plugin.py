from typing import TYPE_CHECKING, List

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

from . import (
    GatewayConfig,
    authorize,
    capture,
    get_client_token,
    list_client_sources,
    process_payment,
    refund,
    void,
)

GATEWAY_NAME = "QPay"

if TYPE_CHECKING:
    # flake8: noqa
    from . import GatewayResponse, PaymentData, TokenConfig
    from ...interface import CustomerSource


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped

# - QPAY_URL=http://43.231.112.201:8080/WebServiceQPayMerchant.asmx
# - QPAY_INVOICE_CODE=TEST_INVOICE
# - QPAY_MERCHANT_CODE=TEST_MERCHANT
# - QPAY_VERIFICATION_CODE=CmqC4uJ3c47unyr2
# - QPAY_AUTH_USER=qpay_test
# - QPAY_AUTH_PASSWORD=sdZv9k9m


class QPayGatewayPlugin(BasePlugin):
    PLUGIN_ID = "endigo.payments.qpay"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_CONFIGURATION = [
        {"name": "API URL", "value": None},
        {"name": "Invoice code", "value": None},
        {"name": "Merchant code", "value": None},
        {"name": "Verification code", "value": None},
        {"name": "Auth username", "value": None},
        {"name": "Auth password", "value": True},
    ]

    CONFIG_STRUCTURE = {
        "API URL": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay API URL",
            "label": "API URL",
        },
        "Invoice code": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay invoice code",
            "label": "Invoice code",
        },
        "Merchant code": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay merchant code",
            "label": "Merchant ID",
        },
        "Verification code": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay verification code",
            "label": "Verification code",
        },
        "Auth username": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay auth username",
            "label": "Auth username",
        },
        "Auth password": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide QPay auth passowrd",
            "label": "Automatic payment capture",
        },
        "Automatic payment capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automaticaly capture payments.",
            "label": "Automatic payment capture",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["Automatic payment capture"],
            connection_params={
                "api_url": configuration["API URL"],
                "invoice_code": configuration["Invoice code"],
                "merchant_code": configuration["Merchant code"],
                "verification_code": configuration["Verification code"],
                "auth_username": configuration["Auth username"],
                "auth_password": configuration["Auth password"],
            },
            store_customer=configuration["Store customers card"],
            require_3d_secure=configuration["Require 3D secure"],
        )

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    @require_active_plugin
    def authorize_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return authorize(payment_information, self._get_gateway_config())

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    @require_active_plugin
    def get_client_token(self, token_config: "TokenConfig", previous_value):
        return get_client_token(self._get_gateway_config(), token_config)

    @require_active_plugin
    def get_payment_config(self, previous_value):
        config = self._get_gateway_config()
        return [
            {"field": "store_customer_card", "value": config.store_customer},
            {"field": "client_token", "value": get_client_token(config=config)},
        ]
