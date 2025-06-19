from fastapi import HTTPException, status


# Excepción que indica que la compra con Transbank no se pudo realizar.
class TransactionTransbankException(Exception):
    def __init__(self):
        self.message = "Transacción con errores transbank"
        super().__init__(self.message)

    def __str__(self):
        return self.message


def request_exception(detail, status_code=status.HTTP_400_BAD_REQUEST):
    return HTTPException(
        detail=detail,
        status_code=status_code,
    )


credentials_exception = request_exception(
    detail="Could not validate credentials.", status_code=status.HTTP_401_UNAUTHORIZED
)

terms_exception = request_exception(
    detail="User has not agreed to the terms.", status_code=status.HTTP_403_FORBIDDEN
)
verified_email_exception = request_exception(
    detail="User has not validated the email.", status_code=status.HTTP_403_FORBIDDEN
)
no_changes_exception = request_exception(
    detail="No changes detected in the update payload.",
    status_code=status.HTTP_400_BAD_REQUEST,
)

no_runners_left_exception = request_exception(
    detail="There must be at least one runner working if restaurant is open.",
    status_code=status.HTTP_400_BAD_REQUEST,
)

active_user_exception = request_exception(
    detail="User is not working at the moment.", status_code=status.HTTP_403_FORBIDDEN
)

permissions_exception = request_exception(
    detail="Your user doesn't have the required permissions to perform this action.",
    status_code=status.HTTP_403_FORBIDDEN,
)

expired_token_exception = request_exception(
    detail="Token has expired.", status_code=status.HTTP_401_UNAUTHORIZED
)

invalid_token_exception = request_exception(
    detail="Invalid token.", status_code=status.HTTP_401_UNAUTHORIZED
)
