from pymysqlreplication import BinLogStreamReader


class CustomBinlogStreamReader(BinLogStreamReader):

    def _register_slave(self):

        # When replicating from Mariadb 10.6.12 using binlog coordinates, a slave capability < 4 triggers a bug in
        # Mariadb, when it tries to replace GTID events with dummy ones. Given that this library understands GTID
        # events, setting the capability to 4 circumvents this error.
        # If the DB is mysql, this won't have any effect so no need to run this in a condition
        cur = self._stream_connection.cursor()
        cur.execute("SET @mariadb_slave_capability=4")
        cur.close()

        super(CustomBinlogStreamReader, self)._register_slave()
