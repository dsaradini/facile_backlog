from django.core.urlresolvers import reverse
from django.core import mail

from django_webtest import WebTest

from facile_backlog.ticketman.models import (Ticket, CATEGORY_CHOICES,
                                             STATUS_CLOSED, STATUS_IN_PROCESS)

import factories


class TicketTest(WebTest):
    def test_create_anonymous_ticket(self):
        user_staff = factories.UserFactory.create(is_staff=True)
        url = reverse("ticket_add")
        response = self.app.get(url)
        form = response.forms["ticket-form"]
        for k, v in {
            'email': 'test@test.com',
            'category': CATEGORY_CHOICES[0][0],
            'text': u"This is a sample message"
        }.iteritems():
            form[k] = v
        response = form.submit().follow()
        self.assertContains(response, "Ticket successfully posted.")
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.email, "test@test.com")
        self.assertEqual(ticket.category, CATEGORY_CHOICES[0][0])
        self.assertEqual(ticket.text, u"This is a sample message")
        message = mail.outbox[-1]
        self.assertIn(user_staff.email, message.to)
        self.assertTrue(
            message.body.find(
                "A new support ticket need to be treated") != -1
        )

    def test_create_user_ticket(self):
        user_staff = factories.UserFactory.create(is_staff=True)
        user = factories.UserFactory.create()
        url = reverse("ticket_add")
        response = self.app.get(url, user=user)
        form = response.forms["ticket-form"]
        for k, v in {
            'category': CATEGORY_CHOICES[0][0],
            'text': u"This is a sample message"
        }.iteritems():
            form[k] = v
        response = form.submit().follow()
        self.assertContains(response, "Ticket successfully posted.")
        self.assertContains(response, "My tickets")
        self.assertContains(response, "This is a sample message")
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.email, user.email)
        message = mail.outbox[-1]
        self.assertIn(user_staff.email, message.to)
        self.assertTrue(
            message.body.find(
                "A new support ticket need to be treated") != -1
        )

    def test_tickets_list(self):
        user_1 = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()
        user_3 = factories.UserFactory.create()
        user_staff = factories.UserFactory.create(is_staff=True)
        Ticket.objects.create(
            email=user_1.email,
            text="Support ticket one",
            category="general"
        )
        ticket_2 = Ticket.objects.create(
            email=user_2.email,
            text="Support ticket two",
            category="general"
        )
        url = reverse("ticket_list")
        response = self.app.get(url)
        self.assertContains(response,
                            "You must be logged-in to see your tickets")
        response = self.app.get(url, user=user_3)
        self.assertContains(response,
                            "You haven't any ticket")
        response = self.app.get(url, user=user_1)
        self.assertContains(response,
                            "My tickets")
        self.assertContains(response,
                            "Support ticket one")
        self.assertNotContains(response,
                               "Support ticket two")

        response = self.app.get(url, user=user_staff)
        self.assertContains(response,
                            "All tickets list")
        self.assertContains(response,
                            "Support ticket one")
        self.assertContains(response,
                            "Support ticket two")
        ticket_2.status = STATUS_CLOSED
        ticket_2.save()
        # Hide closed ticket for staff
        response = self.app.get(url, user=user_staff)
        self.assertContains(response,
                            "All tickets list")
        self.assertContains(response,
                            "Support ticket one")
        self.assertNotContains(response,
                               "Support ticket two")
        # Not for user
        response = self.app.get(url, user=user_2)
        self.assertContains(response,
                            "My tickets")
        self.assertContains(response,
                            "Support ticket two")

    def test_ticket_detail(self):
        user = factories.UserFactory.create()
        user_2 = factories.UserFactory.create()
        user_staff = factories.UserFactory.create(is_staff=True)
        ticket = Ticket.objects.create(
            email=user.email,
            text="Support ticket one",
            category="general"
        )
        url = reverse("ticket_detail", args=(ticket.pk,))
        self.app.get(url, user=user_2, status=404)
        response = self.app.get(url, user=user_staff)
        self.assertContains(response, "Support ticket one")
        # post a message
        form = response.forms["message-form"]
        form['text'] = "Message text one"
        response = form.submit().follow()
        self.assertContains(response, "Message successfully posted.")
        self.assertContains(response, "Message text one")
        ticket = Ticket.objects.get(pk=ticket.pk)
        self.assertEqual(ticket.status, STATUS_IN_PROCESS)
        # An mail to the owner should have been sent
        message = mail.outbox[-1]
        self.assertIn(ticket.email, message.to)

        response = self.app.get(url, user=user)
        self.assertContains(response, "Support ticket one")
        self.assertContains(response, "Message text one")
        # post a message
        form = response.forms["message-form"]
        form['text'] = "Message text two"
        response = form.submit().follow()
        self.assertContains(response, "Message successfully posted.")
        self.assertContains(response, "Message text one")
        self.assertContains(response, "Message text two")

        response = self.app.get(url, user=user_staff)
        self.assertContains(response, "Support ticket one")
        self.assertContains(response, "Message text one")
        # post a message
        form = response.forms["message-form"]
        form['text'] = "Message text two"
        form['close_it'] = True
        response = form.submit().follow()
        ticket = Ticket.objects.get(pk=ticket.pk)
        self.assertEqual(ticket.status, STATUS_CLOSED)
        self.assertContains(response, "Message successfully posted.")
