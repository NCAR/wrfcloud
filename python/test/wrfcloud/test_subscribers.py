import wrfcloud.system
from wrfcloud.subscribers import add_subscriber_to_system
from wrfcloud.subscribers import get_all_subscribers_in_system
from wrfcloud.subscribers import delete_subscriber_from_system
from helper import _test_setup, _test_teardown, _get_sample_subscriber, _get_all_sample_subscribers

# initialize the test environment
wrfcloud.system.init_environment(env='test')


def test_add_subscriber() -> None:
    """
    Test the add subscriber function
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample subscriber
    subscriber = _get_sample_subscriber()

    # add the subscriber to the database
    assert add_subscriber_to_system(subscriber)

    # retrieve the subscriber from the database
    subscribers = get_all_subscribers_in_system()

    # make sure we only got one back
    assert len(subscribers) == 1

    # compare the original and retrieved subscriber data
    subscriber_ = subscribers[0]
    for key in subscriber.data:
        assert key in subscriber_.data
        assert subscriber.data[key] == subscriber_.data[key]

    # teardown the test resources
    assert _test_teardown()


def test_delete_subscriber() -> None:
    """
    Test deleting a subscriber
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # create sample subscriber
    subscribers = _get_all_sample_subscribers()

    # add the subscribers to the database
    for subscriber in subscribers:
        assert add_subscriber_to_system(subscriber)

    # retrieve the subscribers from the database
    subscribers_ = get_all_subscribers_in_system()
    assert subscribers_ is not None
    assert len(subscribers_) == len(subscribers)

    # delete the subscribers one-by-one from the database
    count = len(subscribers)
    for subscriber in subscribers:
        assert delete_subscriber_from_system(subscriber)
        count -= 1
        assert len(get_all_subscribers_in_system()) == count

    # try to delete a with invalid data
    assert not delete_subscriber_from_system(None)

    # teardown the test resources
    assert _test_teardown()


def test_get_all_subscribers() -> None:
    """
    Test the get all subscribers function
    :return: None
    """
    # set up the test resources
    assert _test_setup()

    # get all sample subscribers
    subscribers = _get_all_sample_subscribers()

    # add all the subscribers to the system
    for subscriber in subscribers:
        assert add_subscriber_to_system(subscriber)

    # get all the subscribers in the system
    subscribers_ = get_all_subscribers_in_system()

    # compare the subscribers retrieved to the subscribers expected
    assert len(subscribers) == len(subscribers_)
    for subscriber in subscribers:
        for subscriber_ in subscribers_:
            if subscriber.client_url == subscriber_.client_url:
                assert subscriber.data == subscriber_.data

    # teardown the test resources
    assert _test_teardown()


def test_subscriber_update() -> None:
    """
    Test the update method on the Subscriber class
    """
    subscriber = _get_sample_subscriber()
    client_url = subscriber.client_url
    subscriber.update({'client_url': 'ASDF'})

    assert subscriber.client_url == 'ASDF'
    assert subscriber.client_url != client_url


def test_subscriber_sanitize() -> None:
    """
    Test the sanitize method on the Subscriber class
    """
    subscriber = _get_sample_subscriber()
    sanitized_data = subscriber.sanitized_data
    assert not sanitized_data  # the dictionary should be empty, since we never pass this back to the client
