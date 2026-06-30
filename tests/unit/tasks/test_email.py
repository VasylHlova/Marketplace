import pytest

from app.tasks.email import send_order_confirmation


@pytest.mark.unit
def test_send_order_confirmation(mocker):
    mock_print = mocker.patch("builtins.print")
    send_order_confirmation(buyer_email="customer@example.com", order_id="order_123", total_price=99.99)
    mock_print.assert_called_once()
    called_msg = mock_print.call_args[0][0]
    assert "Confirmation for Order order_123" in called_msg
    assert "customer@example.com" in called_msg
    assert "Total Price: $99.99" in called_msg
