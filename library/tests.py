from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Loan, Book, Member, User, Author
from .tasks import check_overdue_loans

# Create your tests here.

class LibraryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = Author.objects.create(first_name="Peter", last_name="Olayinka")
        self.member = User.objects.create(username="testuser")
        self.book = Book.objects.create(title="Test Book", author=self.author, isbn='fake_isbn')
        self.member = Member.objects.create(user=self.member)

        self.overdue_loan = Loan.objects.create(
            book=self.book,
            member=self.member,
            due_date=timezone.now() - timezone.timedelta(days=1),
            is_returned=False,
        )
        self.returned_loan = Loan.objects.create(
            book=self.book,
            member=self.member,
            due_date=timezone.now() - timezone.timedelta(days=1),
            is_returned=True,
        )
        self.active_loan = Loan.objects.create(
            book=self.book,
            member=self.member,
            due_date=timezone.now() + timezone.timedelta(days=1),
            is_returned=False,
        )

    @patch("library.tasks.send_mail")
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_check_overdue_loans(self, send_mail_mock):
        check_overdue_loans.delay()

        self.assertTrue(send_mail_mock.called)

    def test_extend_additional_days(self):
        response = self.client.patch(
            f"/api/loans/{self.active_loan.id}/extend_due_date/",
            {"additional_days": 36},
        )

        self.assertEqual(response.status_code, 200)

    def test_extend_additional_days_for_overdue_loan(self):
        expected = {'additional_days': ['Loan is already overdue']}
        response = self.client.patch(
            f"/api/loans/{self.overdue_loan.id}/extend_due_date/",
            {"additional_days": 36},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected)

    def test_extend_additional_days_with_negative_number_of_days(self):
        expected = {'additional_days': ['Ensure this value is greater than or equal to 1.']}
        response = self.client.patch(
            f"/api/loans/{self.overdue_loan.id}/extend_due_date/",
            {"additional_days": -23},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), expected)

    @patch("library.tasks.send_mail")
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_assert_number_of_queries_for_overdue_notice(self, send_mail_mock):
        for days in range(10):
            Loan.objects.create(
                book=self.book,
                member=self.member,
                due_date=timezone.now() - timezone.timedelta(days=days),
                is_returned=False,
            )

        with self.assertNumQueries(1):
            check_overdue_loans.delay()

    def test_assert_number_of_queries_for_book_view(self):
        for num in range(10):
            Book.objects.create(title=f"Test Book {num}", author=self.author, isbn=f"isbn_{num}")

        with self.assertNumQueries(2):
            response = self.client.get(
                "/api/books/",
            )
        
        self.assertEqual(response.status_code, 200)

    def test_top_active_loan_members(self):
        expected_active_member_loans = [9, 8, 7, 6, 5]
        for num in range(10):
            user = User.objects.create(username=f"testuser_{num}")
            member = Member.objects.create(user=user)
            for loan in range(num):
                self.overdue_loan = Loan.objects.create(
                    book=self.book,
                    member=member,
                    due_date=timezone.now() + timezone.timedelta(days=loan),
                    is_returned=False,
                )

        with self.assertNumQueries(1):
            response = self.client.get(
                "/api/members/top_active/",
            )

        member_active_loan = [member['active_loans'] for member in response.json()]

        self.assertEqual(member_active_loan, expected_active_member_loans)
        self.assertEqual(response.status_code, 200)
