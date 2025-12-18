/*
 * TestJdbc.java
 *
 * USO:
 * -----
 * Este programa deve ser executado LOCALMENTE
 * na máquina onde o PostgreSQL está rodando.
 *
 * Ele testa:
 * 1) conexão JDBC
 * 2) execução de uma query simples
 *
 * NÃO usar túnel SSH.
 */

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.sql.ResultSet;

public class TestJdbc {

    public static void main(String[] args) {

        // PostgreSQL local (mesma máquina)
        String url =
            "jdbc:postgresql://127.0.0.1:5432/datalake_db"
          + "?sslmode=disable"
          + "&connectTimeout=10"
          + "&socketTimeout=10";

        String user = "datalake_user";
        String password = "senha123";

        // Query de teste
        String sql = "SELECT * FROM \"Fornecedor\" LIMIT 5";

        try {
            System.out.println("Conectando ao PostgreSQL...");
            System.out.println("URL = " + url);

            Connection conn = DriverManager.getConnection(url, user, password);
            System.out.println("Conexão estabelecida com sucesso!");

            // Executa query
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(sql);

            System.out.println("Resultado do SELECT:");
            var meta = rs.getMetaData();
            int colCount = meta.getColumnCount();

            System.out.println("\nColunas:");
            for (int i = 1; i <= colCount; i++) {
                System.out.print(meta.getColumnLabel(i) + "\t");
            }
            System.out.println();

            while (rs.next()) {
                System.out.println(
                    rs.getObject(1) + " | " +
                    rs.getObject(2) + " | " +
                    rs.getObject(3)
                );
            }

            rs.close();
            stmt.close();
            conn.close();

            System.out.println("\nTeste JDBC finalizado com sucesso.");

        } catch (Exception e) {
            System.out.println("Erro durante o teste JDBC:");
            e.printStackTrace();
        }
    }
}
