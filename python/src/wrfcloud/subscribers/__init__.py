"""
Other code calling the wrfcloud.subscribers module should mainly use functions from
this file.  Calling other functions and classes may have unexpected results.
"""
__all__ = ['Subscriber', 'SubscriberDao', 'add_subscriber_to_system',
           'get_all_subscribers_in_system', 'delete_subscriber_from_system']

from typing import List
from wrfcloud.log import Logger
from wrfcloud.subscribers.subscriber import Subscriber
from wrfcloud.subscribers.subscriber_dao import SubscriberDao


log = Logger()


def add_subscriber_to_system(new_subscriber: Subscriber) -> bool:
    """
    Add a subscriber to the system
    :param new_subscriber: The new subscriber to add
    :return True if added successfully
    """
    # get the DAOs
    dao = SubscriberDao()

    # add the subscriber and return status
    return dao.add_subscriber(new_subscriber)


def get_all_subscribers_in_system() -> List[Subscriber]:
    """
    Get a list of all subscribers in the system
    :return: A list of all subscribers in the system
    """
    # create the data access object
    dao = SubscriberDao()

    return dao.get_all_subscribers()


def delete_subscriber_from_system(del_subscriber: Subscriber) -> bool:
    """
    Delete a subscriber from the system
    :param del_subscriber: Job to delete from the system
    :return True if deleted, otherwise False
    """
    # get the subscriber DAO
    dao = SubscriberDao()

    # delete subscriber
    if del_subscriber is not None:
        return dao.delete_subscriber(del_subscriber)

    log.error('Value for subscriber to remove was set as None', ValueError('del_subscriber cannot be None'))
    return False


def message_all_subscribers(message: dict) -> int:
    """
    Send a message to all websocket subscribers
    :param message: Message to send subscribers
    :return: Number of clients reached
    """
    pass
