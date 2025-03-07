# sqlalchemy/pool/events.py
# Copyright (C) 2005-2022 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: https://www.opensource.org/licenses/mit-license.php

from .base import Pool
from .. import event
from .. import util


class PoolEvents(event.Events):
    """Available events for :class:`_pool.Pool`.

    The methods here define the name of an event as well
    as the names of members that are passed to listener
    functions.

    e.g.::

        from sqlalchemy import event

        def my_on_checkout(dbapi_conn, connection_rec, connection_proxy):
            "handle an on checkout event"

        event.listen(Pool, 'checkout', my_on_checkout)

    In addition to accepting the :class:`_pool.Pool` class and
    :class:`_pool.Pool` instances, :class:`_events.PoolEvents` also accepts
    :class:`_engine.Engine` objects and the :class:`_engine.Engine` class as
    targets, which will be resolved to the ``.pool`` attribute of the
    given engine or the :class:`_pool.Pool` class::

        engine = create_engine("postgresql+psycopg2://scott:tiger@localhost/test")

        # will associate with engine.pool
        event.listen(engine, 'checkout', my_on_checkout)

    """  # noqa

    _target_class_doc = "SomeEngineOrPool"
    _dispatch_target = Pool

    @util.preload_module("sqlalchemy.engine")
    @classmethod
    def _accept_with(cls, target):
        Engine = util.preloaded.engine.Engine

        if isinstance(target, type):
            if issubclass(target, Engine):
                return Pool
            elif issubclass(target, Pool):
                return target
        elif isinstance(target, Engine):
            return target.pool
        else:
            return target

    @classmethod
    def _listen(cls, event_key, **kw):
        target = event_key.dispatch_target

        kw.setdefault("asyncio", target._is_asyncio)

        event_key.base_listen(**kw)

    def connect(self, dbapi_connection, connection_record):
        """Called at the moment a particular DBAPI connection is first
        created for a given :class:`_pool.Pool`.

        This event allows one to capture the point directly after which
        the DBAPI module-level ``.connect()`` method has been used in order
        to produce a new DBAPI connection.

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        """

    def first_connect(self, dbapi_connection, connection_record):
        """Called exactly once for the first time a DBAPI connection is
        checked out from a particular :class:`_pool.Pool`.

        The rationale for :meth:`_events.PoolEvents.first_connect`
        is to determine
        information about a particular series of database connections based
        on the settings used for all connections.  Since a particular
        :class:`_pool.Pool`
        refers to a single "creator" function (which in terms
        of a :class:`_engine.Engine`
        refers to the URL and connection options used),
        it is typically valid to make observations about a single connection
        that can be safely assumed to be valid about all subsequent
        connections, such as the database version, the server and client
        encoding settings, collation settings, and many others.

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        """

    def checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Called when a connection is retrieved from the Pool.

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        :param connection_proxy: the :class:`._ConnectionFairy` object which
          will proxy the public interface of the DBAPI connection for the
          lifespan of the checkout.

        If you raise a :class:`~sqlalchemy.exc.DisconnectionError`, the current
        connection will be disposed and a fresh connection retrieved.
        Processing of all checkout listeners will abort and restart
        using the new connection.

        .. seealso:: :meth:`_events.ConnectionEvents.engine_connect`
           - a similar event
           which occurs upon creation of a new :class:`_engine.Connection`.

        """

    def checkin(self, dbapi_connection, connection_record):
        """Called when a connection returns to the pool.

        Note that the connection may be closed, and may be None if the
        connection has been invalidated.  ``checkin`` will not be called
        for detached connections.  (They do not return to the pool.)

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        """

    def reset(self, dbapi_connection, connection_record):
        """Called before the "reset" action occurs for a pooled connection.

        This event represents
        when the ``rollback()`` method is called on the DBAPI connection
        before it is returned to the pool.  The behavior of "reset" can
        be controlled, including disabled, using the ``reset_on_return``
        pool argument.


        The :meth:`_events.PoolEvents.reset` event is usually followed by the
        :meth:`_events.PoolEvents.checkin` event is called, except in those
        cases where the connection is discarded immediately after reset.

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        .. seealso::

            :meth:`_events.ConnectionEvents.rollback`

            :meth:`_events.ConnectionEvents.commit`

        """

    def invalidate(self, dbapi_connection, connection_record, exception):
        """Called when a DBAPI connection is to be "invalidated".

        This event is called any time the :meth:`._ConnectionRecord.invalidate`
        method is invoked, either from API usage or via "auto-invalidation",
        without the ``soft`` flag.

        The event occurs before a final attempt to call ``.close()`` on the
        connection occurs.

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        :param exception: the exception object corresponding to the reason
         for this invalidation, if any.  May be ``None``.

        .. versionadded:: 0.9.2 Added support for connection invalidation
           listening.

        .. seealso::

            :ref:`pool_connection_invalidation`

        """

    def soft_invalidate(self, dbapi_connection, connection_record, exception):
        """Called when a DBAPI connection is to be "soft invalidated".

        This event is called any time the :meth:`._ConnectionRecord.invalidate`
        method is invoked with the ``soft`` flag.

        Soft invalidation refers to when the connection record that tracks
        this connection will force a reconnect after the current connection
        is checked in.   It does not actively close the dbapi_connection
        at the point at which it is called.

        .. versionadded:: 1.0.3

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        :param exception: the exception object corresponding to the reason
         for this invalidation, if any.  May be ``None``.

        """

    def close(self, dbapi_connection, connection_record):
        """Called when a DBAPI connection is closed.

        The event is emitted before the close occurs.

        The close of a connection can fail; typically this is because
        the connection is already closed.  If the close operation fails,
        the connection is discarded.

        The :meth:`.close` event corresponds to a connection that's still
        associated with the pool. To intercept close events for detached
        connections use :meth:`.close_detached`.

        .. versionadded:: 1.1

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        """

    def detach(self, dbapi_connection, connection_record):
        """Called when a DBAPI connection is "detached" from a pool.

        This event is emitted after the detach occurs.  The connection
        is no longer associated with the given connection record.

        .. versionadded:: 1.1

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        :param connection_record: the :class:`._ConnectionRecord` managing the
         DBAPI connection.

        """

    def close_detached(self, dbapi_connection):
        """Called when a detached DBAPI connection is closed.

        The event is emitted before the close occurs.

        The close of a connection can fail; typically this is because
        the connection is already closed.  If the close operation fails,
        the connection is discarded.

        .. versionadded:: 1.1

        :param dbapi_connection: a DBAPI connection.
         The :attr:`._ConnectionRecord.dbapi_connection` attribute.

        """
