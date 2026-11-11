from indico.modules.events.ical import generate_event_component


def test_export_includes_event_category(create_event, create_category):
    category = create_category(title='Seminars')
    event = create_event(category=category)

    exported = generate_event_component(event).to_ical()

    assert b'CATEGORIES:Seminars' in exported.splitlines()


def test_export_skips_category_for_unlisted_event(dummy_event):
    dummy_event.category = None

    component = generate_event_component(dummy_event)

    assert 'CATEGORIES' not in component
