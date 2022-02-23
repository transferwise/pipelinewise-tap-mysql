#!/usr/bin/env python3
# pylint: disable=too-many-locals,missing-function-docstring

import singer

from singer import metadata

import tap_mysql.sync_strategies.binlog as binlog
import tap_mysql.sync_strategies.common as common

from tap_mysql.connection import connect_with_backoff

LOGGER = singer.get_logger('tap_mysql')


def generate_bookmark_keys(catalog_entry):
    md_map = metadata.to_map(catalog_entry.metadata)
    stream_metadata = md_map.get((), {})
    replication_method = stream_metadata.get('replication-method')

    base_bookmark_keys = {'last_pk_fetched', 'version', 'initial_full_table_complete'}

    if replication_method == 'FULL_TABLE':
        bookmark_keys = base_bookmark_keys
    else:
        bookmark_keys = base_bookmark_keys.union(binlog.BOOKMARK_KEYS)

    return bookmark_keys


def pks_are_auto_incrementing(mysql_conn, catalog_entry):
    database_name = common.get_database_name(catalog_entry)
    key_properties = common.get_key_properties(catalog_entry)

    if not key_properties:
        return False

    sql = """SELECT 1
               FROM information_schema.columns
              WHERE table_schema = '{}'
                AND table_name = '{}'
                AND column_name = '{}'
                AND extra LIKE '%auto_increment%'
    """

    with connect_with_backoff(mysql_conn) as open_conn:
        with open_conn.cursor() as cur:
            for primary_key in key_properties:
                cur.execute(sql.format(database_name,
                                       catalog_entry.table,
                                       primary_key))

                result = cur.fetchone()

                if not result:
                    return False

    return True


def sync_table(mysql_conn, catalog_entry, state, columns, stream_version):
    common.whitelist_bookmark_keys(generate_bookmark_keys(catalog_entry), catalog_entry.tap_stream_id, state)

    bookmark = state.get('bookmarks', {}).get(catalog_entry.tap_stream_id, {})
    version_exists = 'version' in bookmark

    initial_full_table_complete = singer.get_bookmark(state,
                                                      catalog_entry.tap_stream_id,
                                                      'initial_full_table_complete')

    state_version = singer.get_bookmark(state,
                                        catalog_entry.tap_stream_id,
                                        'version')

    activate_version_message = singer.ActivateVersionMessage(
        stream=catalog_entry.stream,
        version=stream_version
    )

    # For the initial replication, emit an ACTIVATE_VERSION message
    # at the beginning so the records show up right away.
    if not initial_full_table_complete and not (version_exists and state_version is None):
        singer.write_message(activate_version_message)

    with connect_with_backoff(mysql_conn) as open_conn:
        with open_conn.cursor() as cur:
            select_sql = common.generate_select_sql(catalog_entry, columns)

            params = {}

            common.sync_query(cur,
                              catalog_entry,
                              state,
                              select_sql,
                              columns,
                              stream_version,
                              params)

    singer.write_message(activate_version_message)
