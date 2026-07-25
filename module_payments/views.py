from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from .models import Payment
from .utils import verify_payment


class PaymentCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: None, 400: None})
    def get(self, request):
        authority = request.query_params.get("Authority")
        zp_status = request.query_params.get("Status")

        payment = get_object_or_404(Payment, authority=authority)

        if zp_status != "OK":
            payment.status = Payment.STATUS_FAILED
            payment.save()
            return Response(
                {"detail": "پرداخت توسط کاربر لغو شد یا ناموفق بود"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_success, ref_id = verify_payment(authority, payment.amount)

        if is_success:
            payment.status = Payment.STATUS_SUCCESS
            payment.ref_id = ref_id or ""
            payment.save()

            payment.order.status = payment.order.STATUS_PAID
            payment.order.save()

            return Response({"detail": "پرداخت با موفقیت انجام شد", "ref_id": ref_id})

        payment.status = Payment.STATUS_FAILED
        payment.save()
        return Response(
            {"detail": "تایید پرداخت ناموفق بود"}, status=status.HTTP_400_BAD_REQUEST
        )
