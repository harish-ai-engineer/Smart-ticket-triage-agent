"""Sample tickets used to exercise the triage agent without a live helpdesk feed."""

from datetime import datetime

_RUN_ID = datetime.now().strftime("%H%M%S")

sample_tickets: list[dict] = [
    {
        "ticket_id": f"AF-{_RUN_ID}-001",
        "customer_name": "Nisha Rao",
        "subject": "Missing item in my order",
        "message": (
            "Hi, I received my package today but one item (a pair of earrings) "
            "is missing from the box. Order is ORD-84712. Please help urgently, "
            "this was a gift."
        ),
    },
    {
        "ticket_id": f"AF-{_RUN_ID}-002",
        "customer_name": "Arjun Mehta",
        "subject": "Refund request for Rs 28990 order",
        "message": (
            "I want to return order ORD-61033 and get a full refund of Rs 28990. "
            "The necklace I received doesn't match what was shown on the site."
        ),
    },
    {
        "ticket_id": f"AF-{_RUN_ID}-003",
        "customer_name": "Leela Kapoor",
        "subject": "Question about return policy",
        "message": (
            "Hello, I'm thinking of buying a ring but wanted to check your return "
            "policy first. How many days do I have to return it if it doesn't fit?"
        ),
    },
    {
        "ticket_id": f"AF-{_RUN_ID}-004",
        "customer_name": "Dev Malhotra",
        "subject": "Tracking link is not updating",
        "message": (
            "My order ORD-84712 still shows the same tracking status since yesterday. "
            "Can you please check when it will arrive?"
        ),
    },
    {
        "ticket_id": f"AF-{_RUN_ID}-005",
        "customer_name": "Sara Iyer",
        "subject": "Bracelet arrived damaged",
        "message": (
            "The bracelet in order ORD-61033 arrived with a broken clasp and scratches. "
            "I need a replacement or refund as soon as possible."
        ),
    },
]
