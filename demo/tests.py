from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Aula, Clase, Docente, Horario


class LegacyCatalogMigrationTests(TestCase):
    def test_existing_docentes_and_clases_are_imported_but_aulas_are_not(self):
        self.assertEqual(Docente.objects.count(), 5)
        self.assertEqual(Clase.objects.count(), 4)
        self.assertFalse(Aula.objects.exists())


class AuthenticationTests(TestCase):
    def test_application_routes_require_login(self):
        protected_paths = (
            reverse('home'),
            reverse('formDocente'),
            reverse('formClase'),
            reverse('aulas'),
            reverse('generarHorario'),
            reverse('filtrarHorario'),
            reverse('descargarHorario'),
            reverse('insert_docente'),
            reverse('insert_clase'),
            reverse('insertar_aula'),
        )
        for path in protected_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith(reverse('login')))

    def test_registration_login_and_logout_use_django_sessions(self):
        response = self.client.post(
            reverse('registrarUsuario'),
            {'email': 'coordinador@example.com', 'password': 'Una-clave-segura-481!'},
        )
        self.assertRedirects(response, reverse('login'))
        user = get_user_model().objects.get(email='coordinador@example.com')
        self.assertTrue(user.check_password('Una-clave-segura-481!'))

        response = self.client.post(
            reverse('login'),
            {'email': user.email.upper(), 'password': 'Una-clave-segura-481!'},
        )
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('index'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registration_rejects_duplicate_email_and_weak_password(self):
        get_user_model().objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='Una-clave-segura-481!',
        )
        duplicate = self.client.post(
            reverse('registrarUsuario'),
            {'email': 'EXISTING@example.com', 'password': 'Otra-clave-segura-481!'},
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertFalse(duplicate.context['form'].is_valid())

        weak_password = self.client.post(
            reverse('registrarUsuario'),
            {'email': 'new@example.com', 'password': '123'},
        )
        self.assertEqual(weak_password.status_code, 200)
        self.assertFalse(weak_password.context['form'].is_valid())


class CatalogCrudTests(TestCase):
    def setUp(self):
        Docente.objects.all().delete()
        Clase.objects.all().delete()
        Aula.objects.all().delete()
        self.user = get_user_model().objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='Una-clave-segura-481!',
        )
        self.client.force_login(self.user)

    def test_docente_crud_uses_orm_and_validates_duplicate_primary_key(self):
        response = self.client.post(
            reverse('insert_docente'),
            {'id': '12345', 'nombre': 'Ana', 'apellido': 'Pérez'},
        )
        self.assertRedirects(response, reverse('formDocente'))
        docente = Docente.objects.get(pk='12345')
        self.assertEqual(
            self.client.get(f"{reverse('edit_docente')}?id={docente.pk}").status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"{reverse('remove_docente')}?id={docente.pk}").status_code,
            200,
        )

        invalid = self.client.post(
            reverse('insert_docente'),
            {'id': '12345', 'nombre': 'Otra', 'apellido': 'Persona'},
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(Docente.objects.count(), 1)

        response = self.client.post(
            reverse('update_docente'),
            {'id': docente.pk, 'nombre': 'Ana María', 'apellido': 'Pérez'},
        )
        self.assertRedirects(response, reverse('formDocente'))
        docente.refresh_from_db()
        self.assertEqual(docente.nombre, 'Ana María')

        response = self.client.post(reverse('delete_docente'), {'id': docente.pk})
        self.assertRedirects(response, reverse('formDocente'))
        self.assertFalse(Docente.objects.exists())

    def test_class_crud_persists_numeric_fields_and_rejects_negative_values(self):
        response = self.client.post(
            reverse('insert_clase'),
            {'id': 'IS-101', 'clase': 'Programación', 'uv': '4', 'cantidadEM': '25'},
        )
        self.assertRedirects(response, reverse('formClase'))
        clase = Clase.objects.get(pk='IS-101')
        self.assertEqual((clase.uv, clase.cantidadEM), (4, 25))
        self.assertEqual(
            self.client.get(f"{reverse('edit_clase')}?id={clase.pk}").status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"{reverse('remove_clase')}?id={clase.pk}").status_code,
            200,
        )

        invalid = self.client.post(
            reverse('insert_clase'),
            {'id': 'IS-102', 'clase': 'Matemática', 'uv': '-1', 'cantidadEM': '-4'},
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(Clase.objects.filter(pk='IS-102').exists())

    def test_aula_create_update_and_delete(self):
        response = self.client.post(
            reverse('insertar_aula'),
            {
                'idAula': 'LAB-1',
                'nombreAula': 'Laboratorio de redes',
                'tipo': Aula.Tipo.LABORATORIO,
                'capacidad': '24',
            },
        )
        self.assertRedirects(response, reverse('aulas'))
        aula = Aula.objects.get(pk='LAB-1')
        self.assertEqual(
            self.client.get(reverse('editar_aula', args=[aula.pk])).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('eliminar_aula', args=[aula.pk])).status_code,
            200,
        )

        response = self.client.post(
            reverse('actualizar_aula', args=[aula.pk]),
            {
                'idAula': 'OTHER-ID',
                'nombreAula': 'Laboratorio actualizado',
                'tipo': Aula.Tipo.LABORATORIO,
                'capacidad': '30',
            },
        )
        self.assertRedirects(response, reverse('aulas'))
        aula.refresh_from_db()
        self.assertEqual(aula.pk, 'LAB-1')
        self.assertEqual(aula.capacidad, 30)

        response = self.client.post(
            reverse('confirmar_eliminar_aula', args=[aula.pk]),
        )
        self.assertRedirects(response, reverse('aulas'))
        self.assertFalse(Aula.objects.exists())


class ScheduleTests(TestCase):
    def setUp(self):
        Docente.objects.all().delete()
        Clase.objects.all().delete()
        Aula.objects.all().delete()
        self.user = get_user_model().objects.create_user(
            username='planner@example.com',
            email='planner@example.com',
            password='Una-clave-segura-481!',
        )
        self.client.force_login(self.user)

    def test_schedule_generation_assigns_unique_teachers_and_rooms_per_hour(self):
        Docente.objects.create(id='D1', nombre='Ada', apellido='Lovelace')
        Docente.objects.create(id='D2', nombre='Grace', apellido='Hopper')
        Aula.objects.create(
            idAula='A1',
            nombreAula='Aula 1',
            tipo=Aula.Tipo.AULA,
            capacidad=30,
        )
        Aula.objects.create(
            idAula='A2',
            nombreAula='Aula 2',
            tipo=Aula.Tipo.AULA,
            capacidad=30,
        )
        for code in ('C1', 'C2', 'C3'):
            Clase.objects.create(id=code, clase=f'Clase {code}', uv=3, cantidadEM=20)

        response = self.client.get(reverse('generarHorario'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Horario.objects.count(), 3)
        for hora in Horario.objects.values_list('hora', flat=True).distinct():
            asignaciones = Horario.objects.filter(hora=hora)
            self.assertEqual(
                asignaciones.values('idDocente').distinct().count(),
                asignaciones.count(),
            )
            self.assertEqual(
                asignaciones.values('idAula').distinct().count(),
                asignaciones.count(),
            )
        for asignacion in Horario.objects.select_related('idClase', 'idAula'):
            self.assertGreaterEqual(
                asignacion.idAula.capacidad,
                asignacion.idClase.cantidadEM,
            )
        pdf_response = self.client.get(reverse('descargarHorario'))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')

    def test_schedule_does_not_replace_existing_schedule_if_room_capacity_is_too_small(self):
        docente = Docente.objects.create(id='D1', nombre='Ada', apellido='Lovelace')
        aula = Aula.objects.create(
            idAula='A1',
            nombreAula='Aula 1',
            tipo=Aula.Tipo.AULA,
            capacidad=20,
        )
        clase = Clase.objects.create(
            id='C1',
            clase='Clase C1',
            uv=3,
            cantidadEM=25,
        )
        existing = Horario.objects.create(
            idClase=clase,
            idDocente=docente,
            idAula=aula,
            hora=7,
        )

        response = self.client.get(reverse('generarHorario'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(Horario.objects.all()), [existing])
        self.assertTrue(
            any('capacidad adecuada' in str(message) for message in response.context['messages']),
        )

    def test_invalid_hour_filter_returns_a_message_instead_of_an_error(self):
        response = self.client.get(reverse('filtrarHorario'), {'hora': 'tarde'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['horario'].count(), 0)
