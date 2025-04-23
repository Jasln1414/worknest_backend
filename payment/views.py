from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import razorpay
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import *
from user_account.models import Employer
from Empjob.models import Jobs

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Verify user is an employer
            if request.user.user_type != 'employer':
                return JsonResponse({"success": False, "message": "Only employers can post jobs"}, status=403)
                
            data = request.data
            amount = 200 * 100  # Fixed amount of ₹200 in paisa
            employer_id = data.get("employer_id")
            
            if not employer_id:
                return JsonResponse({"success": False, "message": "Missing employer ID"}, status=400)
            
            try:
                employer = Employer.objects.get(user=request.user)
            except Employer.DoesNotExist:
                return JsonResponse({"success": False, "message": "Employer profile not found"}, status=404)
            
            print(f"Creating order for Employer: {employer_id}, Amount: {amount}")
            
            order_data = {
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1",
                "notes": {
                    "employer_id": employer_id,
                    "purpose": "job_post_payment"
                }
            }
            
            order = razorpay_client.order.create(order_data)
            return JsonResponse(order)
        
        except Exception as e:
            print(f"Error creating order: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)

class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Verify user is an employer
            if request.user.user_type != 'employer':
                return JsonResponse({"success": False, "message": "Only employers can post jobs"}, status=403)
                
            data = request.data
            payment_id = data.get("payment_id")
            order_id = data.get("order_id")
            signature = data.get("signature")
            job_id = data.get("job_id", None)  # Optional for future job reference
            transaction_id = data.get("transaction_id")
            payment_method = data.get("method")
            
            print(f"Verifying payment for Employer: {request.user.id}, Method: {payment_method}")
            
            if not payment_id or not order_id or not signature:
                return JsonResponse({"success": False, "message": "Missing payment details"}, status=400)
            
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
            
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                payment_verified = True
            except razorpay.errors.SignatureVerificationError as e:
                print(f"Payment verification failed: {e}")
                return JsonResponse({"success": False, "message": "Invalid payment signature"}, status=400)
            
            if payment_verified:
                employer = Employer.objects.get(user=request.user)
                job = None
                if job_id:
                    try:
                        job = Jobs.objects.get(id=job_id, employer=employer)
                    except Jobs.DoesNotExist:
                        pass
                
                # Save payment details in the database
                payment = Payment.objects.create(
                    user=request.user,
                    employer=employer,
                    job=job,
                    amount=200,  # Fixed amount of ₹200
                    method=payment_method or "unknown",
                    transaction_id=transaction_id,
                    status="success",
                )
                
                return JsonResponse({
                    "success": True, 
                    "message": "Payment verified successfully!",
                    "payment_id": payment.id
                })
        
        except Exception as e:
            print(f"Error in payment verification: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)
        
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
    

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import SubscriptionPlan, EmployerSubscription, Payment
from user_account.models import Employer
from django.utils import timezone
from datetime import timedelta
import razorpay
from django.conf import settings
from razorpay.errors import BadRequestError, SignatureVerificationError

logger = logging.getLogger(__name__)
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class SubscriptionPlansList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            plans = SubscriptionPlan.objects.all()
            data = [
                {
                    'id': plan.id,
                    'name': plan.get_name_display(),
                    'description': plan.description,
                    'price': plan.price,
                    'job_limit': plan.job_limit,
                }
                for plan in plans
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f'Error fetching plans: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class CreateSubscription(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        plan_id = request.data.get('plan_id')

        if not plan_id:
            return Response({'message': 'Plan ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employer = Employer.objects.get(user=user)
            plan = SubscriptionPlan.objects.get(id=plan_id)

            # Deactivate existing active subscription
            active_sub = EmployerSubscription.objects.filter(
                employer=employer, status="active", end_date__gt=timezone.now()
            ).first()
            if active_sub:
                logger.info(f"Deactivating existing subscription ID: {active_sub.id} for user {user.id}")
                active_sub.status = "inactive"
                active_sub.save()

            # Create Razorpay order
            order_amount = plan.price * 100
            order_data = {
                'amount': order_amount,
                'currency': 'INR',
                'receipt': f'order_rcpt_{employer.id}_{plan.id}',
                'notes': {'plan_id': str(plan.id), 'employer_id': str(employer.id)}
            }
            razorpay_order = razorpay_client.order.create(data=order_data)
            order_id = razorpay_order['id']

            # Create pending payment and subscription
            payment = Payment.objects.create(
                user=user,
                employer=employer,
                amount=plan.price,
                method='Razorpay',
                transaction_id=order_id,
                status='pending',
            )
            subscription = EmployerSubscription.objects.create(
                employer=employer,
                plan=plan,
                end_date=timezone.now() + timedelta(days=plan.duration),
                razorpay_subscription_id=order_id,
                payment=payment,
                status='pending'  # Set to pending until verified
            )

            return Response({
                'message': 'Order created. Please complete payment.',
                'order_id': order_id,
                'amount': order_amount,
                'key_id': settings.RAZORPAY_KEY_ID,
            }, status=status.HTTP_201_CREATED)

        except Employer.DoesNotExist:
            return Response({'message': 'Employer not found.'}, status=status.HTTP_404_NOT_FOUND)
        except SubscriptionPlan.DoesNotExist:
            return Response({'message': 'Invalid plan ID.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return Response({'message': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class VerifyPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return Response({'message': 'Missing required payment parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employer = Employer.objects.get(user=user)
            payment = Payment.objects.get(transaction_id=razorpay_order_id, employer=employer)

            # Verify signature
            params_dict = {
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature,
            }
            razorpay_client.utility.verify_payment_signature(params_dict)

            # Update payment and subscription
            payment.status = 'success'
            payment.transaction_id = razorpay_payment_id
            payment.save()

            subscription = EmployerSubscription.objects.get(
                razorpay_subscription_id=razorpay_order_id, employer=employer
            )
            subscription.status = 'active'
            subscription.save()

            return Response({'message': 'Payment successful. Subscription activated.'}, status=status.HTTP_200_OK)

        except Employer.DoesNotExist:
            return Response({'message': 'Employer not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Payment.DoesNotExist:
            return Response({'message': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)
        except EmployerSubscription.DoesNotExist:
            return Response({'message': 'Subscription record not found.'}, status=status.HTTP_404_NOT_FOUND)
        except razorpay.errors.SignatureVerificationError:
            return Response({'message': 'Payment verification failed - invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in VerifyPayment: {str(e)}")
            return Response({'message': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


from django.db import transaction  # Add this import




class VerifyJobSlotAddOnView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        try:
            payment_id = request.data.get('razorpay_payment_id')
            order_id = request.data.get('razorpay_order_id')
            signature = request.data.get('razorpay_signature')
            
            if not all([payment_id, order_id, signature]):
                return Response(
                    {"error": "Missing payment information"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify payment signature
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            employer = Employer.objects.get(user=request.user)
            add_on = JobSlotAddOn.objects.get(
                order_id=order_id,
                employer=employer,
                status='pending'
            )
            
            subscription = EmployerSubscription.objects.filter(
                employer=employer,
                status='active',
                end_date__gt=timezone.now()
            ).first()
            
            if not subscription:
                return Response(
                    {"error": "No active subscription found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # All these updates happen atomically
            add_on.razorpay_payment_id = payment_id
            add_on.razorpay_signature = signature
            add_on.status = 'completed'
            add_on.save()
            
            subscription.job_limit += add_on.job_count
            subscription.save()
            
            # Create Payment record - removed 'purpose' parameter
            Payment.objects.create(
                user=request.user,
                employer=employer,
                amount=add_on.amount,
                method='Razorpay',
                transaction_id=payment_id,
                status='success'
            )
            
            return Response({
                "success": True,
                "message": f"Successfully added {add_on.job_count} job slots",
                "new_job_limit": subscription.job_limit
            }, status=status.HTTP_200_OK)
            
        except JobSlotAddOn.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except razorpay.errors.SignatureVerificationError:
            logger.error("Payment signature verification failed")
            return Response({"error": "Invalid payment signature"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AddJobSlotsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            employer = Employer.objects.get(user=request.user)
            job_count = request.data.get('job_count')
            
            if not job_count:
                return Response({"error": "job_count is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                job_count = int(job_count)
                if job_count <= 0:
                    return Response({"error": "Job count must be positive"}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({"error": "job_count must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
            
            active_subscription = EmployerSubscription.objects.filter(
                employer=employer,
                status='active',
                end_date__gt=timezone.now()
            ).first()
            
            if not active_subscription:
                return Response({
                    "error": "No active subscription found",
                    "subscription_required": True
                }, status=status.HTTP_402_PAYMENT_REQUIRED)
            
            if active_subscription.job_limit == 9999:  # Check subscription.job_limit, not plan
                return Response({
                    "error": "You have an unlimited plan",
                    "message": "No need to purchase additional slots"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            price_per_job = 200
            total_amount = price_per_job * job_count
            
            order = razorpay_client.order.create({
                "amount": total_amount * 100,  # Convert to paise
                "currency": "INR",
                "payment_capture": 1,
                "notes": {"job_count": str(job_count), "employer_id": str(employer.id)}
            })
            
            JobSlotAddOn.objects.create(
                employer=employer,
                subscription=active_subscription,
                job_count=job_count,
                amount=total_amount,
                order_id=order['id'],
                status='pending'
            )
            
            return Response({
                "order_id": order['id'],
                "amount": order['amount'],
                "key_id": settings.RAZORPAY_KEY_ID,
                "job_count": job_count
            }, status=status.HTTP_201_CREATED)
            
        except Employer.DoesNotExist:
            return Response({"error": "Employer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error adding job slots: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)