package org.apache.ctakes.dictionary.lookup2.util;

import java.sql.*;


//https://jdbc.postgresql.org/documentation/81/listennotify.html

class Listener extends Thread {

	private Connection conn;
	private org.postgresql.PGConnection pgconn;

	Listener(Connection conn) throws SQLException {
		this.conn = conn;
		this.pgconn = (org.postgresql.PGConnection)conn;
		Statement stmt = conn.createStatement();
		stmt.execute("LISTEN mymessage");
		stmt.close();
	}

	public void run() {
		while (true) {
			try {
				// issue a dummy query to contact the backend
				// and receive any pending notifications.
				Statement stmt = conn.createStatement();
				ResultSet rs = stmt.executeQuery("SELECT 1");
				System.out.println(rs.toString());
				Thread.sleep(30000);
				rs.close();
				stmt.close();

				org.postgresql.PGNotification notifications[] = pgconn.getNotifications();
				if (notifications != null) {
					for (int i=0; i<notifications.length; i++) {
						System.out.println("Got notification: " + notifications[i].getName());
					}
				}

				
			} catch (SQLException sqle) {
				sqle.printStackTrace();
				
				Thread.currentThread().interrupt();
			} catch (InterruptedException ie) {
				ie.printStackTrace();
				Thread.currentThread().interrupt();
			}
		}
	}

}