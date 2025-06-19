from typing import Optional
from sqlalchemy.future import select
from fastapi import Depends
from dependencies.session import get_generic_session
from shared_models.transactions import (
    Transaction,
    TransactionWebpay,
    TransactionWebpayMall,
)
from repository.session import SessionDAL

"""
def get_transaction_instance_from_token_using_query(token_ws: Optional[str] = None,
                                                    TBK_TOKEN: Optional[str] = None,
                                                    session: SessionDAL = Depends(get_generic_session)):
    def get_from_token(token_ws: str, session: SessionDAL):
        select_query = (
            select(Transaction)
            .where(Transaction.token_ws==token_ws)
            .order_by(Transaction.created_at.asc())
        )
        return session.get(select_query)
    token = token_ws if token_ws else TBK_TOKEN
    return get_model_instance(get_from_token, token, session=session)
"""


def get_transaction_instance_from_token_using_query(
    token_ws: Optional[str] = None,
    TBK_TOKEN: Optional[str] = None,
    session: SessionDAL = Depends(get_generic_session),
):
    def get_from_token(token_ws: str, session: SessionDAL):
        select_query = (
            select(TransactionWebpay)
            .where(TransactionWebpay.token_ws == token_ws)
            .order_by(TransactionWebpay.created_at.asc())
        )
        return session.get(select_query)

    def get_from_token_mall(token_ws: str, session: SessionDAL):
        select_query = (
            select(TransactionWebpayMall)
            .where(TransactionWebpayMall.token_ws == token_ws)
            .order_by(TransactionWebpayMall.created_at.asc())
        )
        return session.get(select_query)

    token = token_ws if token_ws else TBK_TOKEN
    if not token:
        return None, None, None
    transaction_webpay_instance = get_from_token(token, session)
    commerce_code = None
    if not transaction_webpay_instance:
        transaction_webpay_instance = get_from_token_mall(token, session)
        commerce_code = transaction_webpay_instance.commerce_code

    select_query = select(Transaction).where(
        Transaction.id == transaction_webpay_instance.transaction_id
    )
    transaction_instance = session.get(select_query)

    return transaction_instance, transaction_webpay_instance, commerce_code
