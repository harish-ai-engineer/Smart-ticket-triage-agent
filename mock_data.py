"""Sample tickets used to exercise the triage agent without a live helpdesk feed."""

sample_tickets: list[dict] = [
    {
        "ticket_id": "TKT-001",
        "customer_name": "Priya M.",
        "subject": "Missing item in my order",
        "message": (
            "Hi, I received my package today but one item (a pair of earrings) "
            "is missing from the box. Order is ORD-84712. Please help urgently, "
            "this was a gift."
        ),
    },
    {
        "ticket_id": "TKT-002",
        "customer_name": "Ravi K.",
        "subject": "Refund request for Rs 28990 order",
        "message": (
            "I want to return order ORD-61033 and get a full refund of Rs 28990. "
            "The necklace I received doesn't match what was shown on the site."
        ),
    },
    {
        "ticket_id": "TKT-003",
        "customer_name": "Ananya S.",
        "subject": "Question about return policy",
        "message": (
            "Hello, I'm thinking of buying a ring but wanted to check your return "
            "policy first. How many days do I have to return it if it doesn't fit?"
        ),
    },
]
