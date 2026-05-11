from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json
import secrets
from .models import Client, Car, Order, User, ScheduleShift, Role, Manager, Master
from .decorators import role_required


def set_user_session(request, user):
    request.session["user_id"] = user.id
    request.session["role_id"] = user.role_id.id
    request.session["user_role"] = user.role_id.name
    request.session["user_name"] = user.name
    request.session["user_surname"] = user.surname


def home_page(request):
    return render(request, 'base.html')


@role_required('client', 'manager', 'admin', 'master')
def orders_page(request):
    status_filter = request.GET.get('status', 'all')
    user_role = request.session.get("user_role")
    session_user_id = request.session.get("user_id")

    if request.method == "POST":
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        car_brand = request.POST.get('car_brand')
        car_model = request.POST.get('car_model')
        car_plate = request.POST.get('car_plate')
        vin = request.POST.get('vin', '')
        car_year = request.POST.get('car_year', None)
        car_color = request.POST.get('car_color', '')
        problem_desc = request.POST.get('problem_desc', '')

        if user_role == "client":
            current_user = User.objects.select_related("role_id").get(id=session_user_id)
            current_client = Client.objects.get(user_id=current_user)

            name = current_user.name
            surname = current_user.surname
            email = current_user.email
            phone = current_client.phone

        required_fields = [name, surname, email, phone, car_brand, car_model, car_plate]

        if not all(required_fields):
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('/orders/')

        try:
            with transaction.atomic():
                user = User.objects.select_related("role_id").filter(email=email).first()

                if not user:
                    client_role = Role.objects.get(name="client")

                    user = User(
                        name=name,
                        surname=surname,
                        email=email,
                        role_id=client_role
                    )

                    temp_password = secrets.token_urlsafe(8)
                    print(f"INFO: Новый пользователь {email}, временный пароль: {temp_password}")

                    user.set_password(temp_password)
                    user.save()

                    messages.success(request, f'Новый пользователь {surname} {name} создан!')
                else:
                    messages.info(request, f'Добро пожаловать, {user.surname} {user.name}!')

                client, created = Client.objects.get_or_create(
                    user_id=user,
                    defaults={'phone': phone}
                )

                if not created and client.phone != phone:
                    client.phone = phone
                    client.save()

                existing_car = Car.objects.filter(plate_number=car_plate.upper()).first()

                if existing_car:
                    if existing_car.client_id == user.id:
                        car = existing_car
                        messages.info(request, f'Машина {car_plate} уже есть в системе')
                    else:
                        owner = User.objects.filter(id=existing_car.client_id).first()
                        owner_name = f'{owner.surname} {owner.name}' if owner else 'другим клиентом'
                        messages.error(request, f'Машина с госномером {car_plate} закреплена за {owner_name}')
                        return redirect('/orders/')
                else:
                    car = Car.objects.create(
                        client_id=user.id,
                        brand=car_brand,
                        model=car_model,
                        vin=vin if vin else None,
                        plate_number=car_plate.upper(),
                        year_produced=car_year if car_year else None,
                        color=car_color if car_color else None
                    )

                order = Order.objects.create(
                    client_id=client,
                    car_id=car,
                    problem_desc=problem_desc,
                    status_id=1
                )

                messages.success(request, f'Заявка #{order.id} успешно создана!')
                return redirect('/orders/')

        except IntegrityError as e:
            messages.error(request, f'Ошибка целостности данных: {e}')
            return redirect('/orders/')
        except Exception as e:
            messages.error(request, f'Неизвестная ошибка: {e}')
            return redirect('/orders/')

    orders_all = Order.objects.select_related(
        'client_id',
        'client_id__user_id',
        'car_id'
    ).order_by('-created_at')

    if user_role == "client":
        orders_all = orders_all.filter(client_id__user_id=session_user_id)

    if status_filter != 'all':
        orders = orders_all.filter(status_id=status_filter)
    else:
        orders = orders_all

    orders_new = orders_all.filter(status_id=1)
    orders_work = orders_all.filter(status_id=2)
    orders_done = orders_all.filter(status_id=3)

    client_phone = ""
    client_email = ""

    if session_user_id:
        current_user = User.objects.filter(id=session_user_id).first()
        current_client = Client.objects.filter(user_id=current_user).first()

        if current_user:
            client_email = current_user.email

        if current_client:
            client_phone = current_client.phone

    return render(request, 'orders.html', {
        'orders': orders,
        'orders_all': orders_all,
        'statuses': {1: 'Новая', 2: 'В работе', 3: 'Завершена'},
        'current_status': status_filter,
        'orders_new': orders_new,
        'orders_work': orders_work,
        'orders_done': orders_done,
        'client_phone': client_phone,
        'client_email': client_email,
    })


def edit_order(request, order_id):
    order = Order.objects.select_related(
        'client_id',
        'client_id__user_id',
        'car_id'
    ).filter(id=order_id).first()

    if not order:
        messages.error(request, 'Заявка не найдена')
        return redirect('/orders/')

    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")

    if not user_id:
        messages.error(request, 'Сначала войдите в аккаунт')
        return redirect('/')

    if user_role == "client" and order.client_id.user_id.id != user_id:
        messages.error(request, 'У вас нет доступа к этой заявке')
        return redirect('/orders/')

    if request.method == "POST":
        problem_desc = request.POST.get('problem_desc', '')

        try:
            with transaction.atomic():
                order.problem_desc = problem_desc

                if user_role in ["manager", "admin"]:
                    status_id = request.POST.get('status_id', order.status_id)

                    if str(status_id) not in {'1', '2', '3'}:
                        messages.error(request, 'Недопустимый статус заявки')
                        return redirect('/orders/')

                    order.status_id = int(status_id)

                order.save()
                messages.success(request, f'Заявка #{order.id} успешно обновлена!')
                return redirect('/orders/')

        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {str(e)}')
            return redirect('/orders/')

    return render(request, 'edit_order.html', {'order': order})


def get_client_by_phone(request):
    phone = request.GET.get('phone', '')

    if phone:
        client = Client.objects.filter(phone=phone).select_related('user_id').first()

        if client:
            return JsonResponse({
                'found': True,
                'name': client.user_id.name,
                'surname': client.user_id.surname,
                'email': client.user_id.email,
                'phone': client.phone,
                'client_id': client.user_id.id
            })

    return JsonResponse({'found': False})


def get_car_by_plate(request):
    plate = request.GET.get('plate', '').upper()

    if plate:
        car = Car.objects.filter(plate_number=plate).first()

        if car:
            owner = User.objects.filter(id=car.client_id).first()

            return JsonResponse({
                'found': True,
                'brand': car.brand,
                'model': car.model,
                'vin': car.vin or '',
                'year': car.year_produced,
                'color': car.color or '',
                'owner_client_id': car.client_id,
                'owner_name': f"{owner.surname} {owner.name}" if owner else 'неизвестен'
            })

    return JsonResponse({'found': False})


def check_plate_owner(request):
    plate = request.GET.get('plate', '').upper()
    current_client_id = request.GET.get('client_id', None)

    if plate:
        car = Car.objects.filter(plate_number=plate).first()

        if car:
            if current_client_id and str(car.client_id) == current_client_id:
                return JsonResponse({
                    'is_owner': True,
                    'message': 'Это ваша машина',
                })

            owner = User.objects.filter(id=car.client_id).first()

            return JsonResponse({
                'is_owner': False,
                'owner_name': f"{owner.surname} {owner.name}" if owner else 'другим клиентом',
                'message': f'Машина закреплена за {owner.surname} {owner.name}' if owner else 'Машина закреплена за другим клиентом'
            })

    return JsonResponse({'is_owner': True, 'message': ''})


@role_required('manager', 'master', 'admin')
def schedule_page(request):
    user_role = request.session.get("user_role")

    if request.method == "POST":
        if user_role not in ["manager"]:
            messages.error(request, "У вас нет прав изменять расписание")
            return redirect("/schedule/")

        employee_id = request.POST.get("employee_id")
        date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")

        if not employee_id or not date or not start_time or not end_time:
            messages.error(request, "Заполните все поля")
            return redirect("/schedule/")

        employee = Master.objects.select_related("user_id").filter(user_id=employee_id).first()

        if not employee:
            messages.error(request, "Мастер не найден")
            return redirect("/schedule/")

        ScheduleShift.objects.create(
            employee=employee,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status="draft"
        )

        messages.success(request, "Смена добавлена")
        return redirect(request.META.get("HTTP_REFERER", "/schedule/"))

    period = request.GET.get("period", "week")
    start_param = request.GET.get("start")

    if start_param:
        start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()
        start_date = today - timedelta(days=today.weekday())

    if period == "month":
        start_date = start_date.replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1)
        days_count = (end_date - start_date).days
    else:
        period = "week"
        end_date = start_date + timedelta(days=7)
        days_count = 7

    date_list = [start_date + timedelta(days=i) for i in range(days_count)]

    shifts = ScheduleShift.objects.select_related(
        "employee",
        "employee__user_id"
    ).filter(
        date__gte=start_date,
        date__lt=end_date
    ).order_by("date", "start_time")

    employees = Master.objects.select_related("user_id").order_by(
        "user_id__surname",
        "user_id__name"
    )

    if period == "month":
        prev_date = (start_date - timedelta(days=1)).replace(day=1)
        next_date = end_date
    else:
        prev_date = start_date - timedelta(days=7)
        next_date = start_date + timedelta(days=7)

    return render(request, "schedule.html", {
        "employees": employees,
        "shifts": shifts,
        "date_list": date_list,
        "period": period,
        "start_date": start_date,
        "prev_date": prev_date.strftime("%Y-%m-%d"),
        "next_date": next_date.strftime("%Y-%m-%d"),
        "can_edit_schedule": user_role in ["manager", "admin"],
    })


@role_required('manager', 'admin', 'master')
def repair_page(request):
    order = {
        'id': 105,
        'plate': 'А777АА 777',
        'damage_initial': 'Вмятина на заднем крыле'
    }

    report_data = {
        'obd_codes': ['P0300', 'P0420'],
        'interior_problems': ['Порвана обивка сиденья', 'Потертость руля'],
        'component_problems': ['Неисправность катушки зажигания', 'Износ тормозных колодок']
    }

    return render(request, 'repair.html', {
        'order': order,
        'has_report': True,
        'report': report_data
    })


@csrf_exempt
def register_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не разрешён"}, status=405)

    data = json.loads(request.body)

    name = data.get("first_name", "").strip()
    surname = data.get("last_name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    password2 = data.get("password2", "")

    if not name or not surname or not phone or not email or not password:
        return JsonResponse({"error": "Заполните все поля"}, status=400)

    if password != password2:
        return JsonResponse({"error": "Пароли не совпадают"}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Пользователь уже существует"}, status=400)

    try:
        with transaction.atomic():
            client_role = Role.objects.get(name="client")

            user = User(
                name=name,
                surname=surname,
                email=email,
                role_id=client_role
            )
            user.set_password(password)
            user.save()

            Client.objects.create(
                user_id=user,
                phone=phone
            )

            set_user_session(request, user)

            return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не разрешён"}, status=405)

    data = json.loads(request.body)

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.objects.select_related("role_id").filter(email=email).first()

    if user and user.check_password(password):
        set_user_session(request, user)
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Неверная почта или пароль"}, status=400)


def logout_view(request):
    request.session.flush()
    return JsonResponse({"success": True})


@role_required('manager')
def delete_shift(request, shift_id):
    shift = ScheduleShift.objects.filter(id=shift_id).first()

    if shift:
        shift.delete()
        messages.success(request, "Смена удалена")

    return redirect(request.META.get("HTTP_REFERER", "/schedule/"))


@role_required('manager')
def publish_schedule(request):
    ScheduleShift.objects.filter(status="draft").update(status="published")
    messages.success(request, "Расписание опубликовано")
    return redirect(request.META.get("HTTP_REFERER", "/schedule/"))


@csrf_exempt
@role_required('manager')
def register_staff_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Метод не разрешён"}, status=405)

    data = json.loads(request.body)

    name = data.get("first_name", "").strip()
    surname = data.get("last_name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role_name = data.get("role", "").strip()

    allowed_roles = ["master", "manager"]

    if role_name not in allowed_roles:
        return JsonResponse({"error": "Менеджер может создавать только мастеров и менеджеров"}, status=400)

    if not name or not surname or not phone or not email or not password:
        return JsonResponse({"error": "Заполните все поля"}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Пользователь уже существует"}, status=400)

    try:
        with transaction.atomic():
            role = Role.objects.get(name=role_name)

            user = User(
                name=name,
                surname=surname,
                email=email,
                role_id=role
            )
            user.set_password(password)
            user.save()

            if role_name == "master":
                raw_is_admin = data.get("is_admin", False)
                is_admin = raw_is_admin in ["true", "True", "1", 1, True, "on"]

                Master.objects.create(
                    user_id=user,
                    qualify_id=None,
                    phone=phone,
                    is_admin=is_admin
                )

            elif role_name == "manager":
                Manager.objects.create(
                    user_id=user,
                    work_phone=phone
                )

            return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)