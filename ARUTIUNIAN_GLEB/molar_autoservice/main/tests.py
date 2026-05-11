from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from .models import User, Client, Car, Order


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'name': 'Иван',
            'surname': 'Петров',
            'email': 'ivan@test.ru'
        }
    
    def test_create_user(self):
        user = User.objects.create(**self.user_data)
        user.set_password('testpass123')
        user.save()
        
        self.assertEqual(user.name, 'Иван')
        self.assertEqual(user.surname, 'Петров')
        self.assertEqual(user.email, 'ivan@test.ru')
        self.assertTrue(check_password('testpass123', user.hash_passwd))
    
    def test_user_str_method(self):
        user = User.objects.create(**self.user_data)
        self.assertEqual(str(user), 'Петров Иван')
    
    def test_user_email_unique(self):
        User.objects.create(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create(**self.user_data)


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name='Иван',
            surname='Петров',
            email='ivan@test.ru'
        )
    
    def test_create_client(self):
        client = Client.objects.create(
            user_id=self.user,
            phone='+79991234567'
        )
        self.assertEqual(client.phone, '+79991234567')
        self.assertEqual(client.user_id.name, 'Иван')


class CarModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name='Иван',
            surname='Петров',
            email='ivan@test.ru'
        )
    
    def test_create_car(self):
        car = Car.objects.create(
            client_id=self.user.id,
            brand='Toyota',
            model='Camry',
            plate_number='А123ВС77',
            vin='12345678901234567'
        )
        self.assertEqual(car.brand, 'Toyota')
        self.assertEqual(car.model, 'Camry')
        self.assertEqual(car.plate_number, 'А123ВС77')
    
    def test_car_plate_unique(self):
        Car.objects.create(
            client_id=self.user.id,
            brand='Toyota',
            model='Camry',
            plate_number='А123ВС77'
        )
        with self.assertRaises(Exception):
            Car.objects.create(
                client_id=self.user.id,
                brand='BMW',
                model='X5',
                plate_number='А123ВС77'
            )


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name='Иван',
            surname='Петров',
            email='ivan@test.ru'
        )
        self.client_obj = Client.objects.create(
            user_id=self.user,
            phone='+79991234567'
        )
        self.car = Car.objects.create(
            client_id=self.user.id,
            brand='Toyota',
            model='Camry',
            plate_number='А123ВС77'
        )
    
    def test_create_order(self):
        order = Order.objects.create(
            client_id=self.client_obj,
            car_id=self.car.id,
            problem_desc='Не заводится',
            status_id=1
        )
        self.assertEqual(order.problem_desc, 'Не заводится')
        self.assertEqual(order.status_id, 1)
        self.assertIsNotNone(order.created_at)
    
    def test_order_str_method(self):
        order = Order.objects.create(
            client_id=self.client_obj,
            car_id=self.car.id,
            problem_desc='Не заводится',
            status_id=1
        )
        self.assertEqual(str(order), f'Заказ #{order.id}')


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            name='Иван',
            surname='Петров',
            email='ivan@test.ru'
        )
        self.user.set_password('testpass123')
        self.user.save()
        
        self.client_obj = Client.objects.create(
            user_id=self.user,
            phone='+79991234567'
        )
        
        self.car = Car.objects.create(
            client_id=self.user.id,
            brand='Toyota',
            model='Camry',
            plate_number='А123ВС77'
        )
        
        self.order = Order.objects.create(
            client_id=self.client_obj,
            car_id=self.car.id,
            problem_desc='Не заводится',
            status_id=1
        )
    
    def test_orders_page_get(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders.html')
    
    def test_orders_page_post_new_user(self):
        data = {
            'name': 'Алексей',
            'surname': 'Сидоров',
            'email': 'alex@test.ru',
            'phone': '+79998887766',
            'car_brand': 'BMW',
            'car_model': 'X5',
            'car_plate': 'В456ЕК77',
            'vin': '12345678901234567',
            'car_year': '2020',
            'car_color': 'Черный',
            'problem_desc': 'Стук в подвеске'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='alex@test.ru').exists())
        self.assertTrue(Order.objects.filter(problem_desc='Стук в подвеске').exists())
    
    def test_orders_page_post_existing_user(self):
        data = {
            'name': 'Иван',
            'surname': 'Петров',
            'email': 'ivan@test.ru',
            'phone': '+79991234567',
            'car_brand': 'Toyota',
            'car_model': 'Camry',
            'car_plate': 'А123ВС77',
            'problem_desc': 'Новая проблема'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(problem_desc='Новая проблема').exists())
    
    def test_orders_page_post_missing_fields(self):
        data = {
            'name': 'Иван',
            'surname': 'Петров',
            'email': 'ivan@test.ru'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('заполните все поля' in str(m) for m in messages))
    
    def test_edit_order_get(self):
        response = self.client.get(f'/edit/{self.order.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_order.html')
    
    def test_edit_order_post(self):
        data = {
            'problem_desc': 'Обновленное описание',
            'status_id': '2'
        }
        response = self.client.post(f'/edit/{self.order.id}/', data)
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.problem_desc, 'Обновленное описание')
        self.assertEqual(self.order.status_id, 2)
    
    def test_edit_order_not_found(self):
        response = self.client.get('/edit/999/')
        self.assertEqual(response.status_code, 302)
    
    def test_get_client_by_phone_found(self):
        response = self.client.get(f'/get-client-by-phone/?phone=+79991234567')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['name'], 'Иван')
        self.assertEqual(data['surname'], 'Петров')
    
    def test_get_client_by_phone_not_found(self):
        response = self.client.get('/get-client-by-phone/?phone=+79990000000')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['found'])
    
    def test_get_car_by_plate_found(self):
        response = self.client.get('/get-car-by-plate/?plate=А123ВС77')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['found'])
        self.assertEqual(data['brand'], 'Toyota')
        self.assertEqual(data['model'], 'Camry')
    
    def test_get_car_by_plate_not_found(self):
        response = self.client.get('/get-car-by-plate/?plate=Х000ХХ00')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['found'])
    
    def test_check_plate_owner_is_owner(self):
        response = self.client.get(f'/check-plate-owner/?plate=А123ВС77&client_id={self.user.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_owner'])
    
    def test_check_plate_owner_not_owner(self):
        response = self.client.get('/check-plate-owner/?plate=А123ВС77&client_id=999')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['is_owner'])
    
    def test_duplicate_car_plate_error(self):
        Car.objects.create(
            client_id=999,
            brand='Honda',
            model='Civic',
            plate_number='Х000ХХ00'
        )
        
        data = {
            'name': 'Дмитрий',
            'surname': 'Кузнецов',
            'email': 'dima@test.ru',
            'phone': '+79991112233',
            'car_brand': 'Honda',
            'car_model': 'Civic',
            'car_plate': 'Х000ХХ00',
            'problem_desc': 'Проблема'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('закреплена' in str(m) for m in messages))
    
    def test_filter_orders_by_status(self):
        Order.objects.create(
            client_id=self.client_obj,
            car_id=self.car.id,
            problem_desc='Тестовая',
            status_id=2
        )
        
        response = self.client.get('/?status=2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая')


class APITest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            name='Тест',
            surname='Тестов',
            email='test@test.ru'
        )
        self.client_obj = Client.objects.create(
            user_id=self.user,
            phone='+79990000000'
        )
    
    def test_get_client_by_phone_api_format(self):
        response = self.client.get('/get-client-by-phone/?phone=+79990000000')
        self.assertEqual(response.status_code, 200)
        self.assertIn('found', response.json())
        self.assertIn('name', response.json())
        self.assertIn('surname', response.json())
        self.assertIn('email', response.json())
    
    def test_get_car_by_plate_api_format(self):
        Car.objects.create(
            client_id=self.user.id,
            brand='Test',
            model='Test',
            plate_number='Т001ТТ01'
        )
        response = self.client.get('/get-car-by-plate/?plate=Т001ТТ01')
        self.assertEqual(response.status_code, 200)
        self.assertIn('found', response.json())
        self.assertIn('brand', response.json())
        self.assertIn('model', response.json())
    
    def test_check_plate_owner_api_format(self):
        Car.objects.create(
            client_id=self.user.id,
            brand='Test',
            model='Test',
            plate_number='Т001ТТ01'
        )
        response = self.client.get('/check-plate-owner/?plate=Т001ТТ01&client_id=999')
        self.assertEqual(response.status_code, 200)
        self.assertIn('is_owner', response.json())
        self.assertIn('message', response.json())


class EdgeCasesTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_empty_form_submission(self):
        response = self.client.post('/', {})
        self.assertEqual(response.status_code, 302)
    
    def test_invalid_email_format(self):
        data = {
            'name': 'Тест',
            'surname': 'Тестов',
            'email': 'invalid-email',
            'phone': '+79990000000',
            'car_brand': 'Toyota',
            'car_model': 'Camry',
            'car_plate': 'А123ВС77',
            'problem_desc': 'Тест'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
    
    def test_very_long_text(self):
        long_text = 'A' * 1000
        data = {
            'name': 'Тест',
            'surname': 'Тестов',
            'email': 'test@test.ru',
            'phone': '+79990000000',
            'car_brand': 'Toyota',
            'car_model': 'Camry',
            'car_plate': 'А123ВС77',
            'problem_desc': long_text
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
    
    def test_special_chars_in_phone(self):
        data = {
            'name': 'Тест',
            'surname': 'Тестов',
            'email': 'test@test.ru',
            'phone': 'abc!@#',
            'car_brand': 'Toyota',
            'car_model': 'Camry',
            'car_plate': 'А123ВС77',
            'problem_desc': 'Тест'
        }
        response = self.client.post('/', data)
        self.assertEqual(response.status_code, 302)
