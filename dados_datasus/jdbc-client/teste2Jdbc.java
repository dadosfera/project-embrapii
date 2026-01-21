/*
 * teste2Jdbc.java
 *
 * USO:
 * -----
 * Este programa deve ser executado NA MÁQUINA LOCAL
 * com um túnel SSH previamente aberto.
 *
 * O JDBC se conecta APENAS a 127.0.0.1:5433
 * (lado local do túnel).
 */

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.sql.ResultSet;

public class teste2Jdbc {

    public static void main(String[] args) {

        // -------------------------------------------------------------
        // URL JDBC USANDO TÚNEL SSH
        //
        // 127.0.0.1 : máquina local
        // 5433      : porta local do túnel
        // -------------------------------------------------------------
        String url =
            "jdbc:postgresql://127.0.0.1:5433/datalake_db"
          + "?sslmode=disable"
          + "&connectTimeout=10"
          + "&socketTimeout=10";

        // Usuário do PostgreSQL (existente no servidor)
        String user = "datalake_user";

        // Senha do usuário
        String password = "senha123";

        try {
            System.out.println("Conectando via túnel SSH...");
            System.out.println("URL JDBC = " + url);

            // -------------------------------------------------------------
            // Abre a conexão JDBC (entra no túnel SSH)
            // -------------------------------------------------------------
            Connection conn = DriverManager.getConnection(url, user, password);
            System.out.println("Conexão estabelecida com sucesso!");

            // -------------------------------------------------------------
            // Cria Statement
            // -------------------------------------------------------------
            Statement stmt = conn.createStatement();

            // -------------------------------------------------------------
            // Query de teste
            // -------------------------------------------------------------
            String sql = "SELECT * FROM \"Fornecedor\" LIMIT 5";

            // -------------------------------------------------------------
            // Executa query
            // -------------------------------------------------------------
            ResultSet rs = stmt.executeQuery(sql);

            // -------------------------------------------------------------
            // Imprime nomes das colunas + primeira linha
            // -------------------------------------------------------------
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
            // -------------------------------------------------------------
            // Fecha recursos
            // -------------------------------------------------------------
            rs.close();
            stmt.close();
            conn.close();

            System.out.println("\nTeste via túnel SSH finalizado com sucesso.");

        } catch (Exception e) {
            System.out.println("Falha ao conectar ou executar query via túnel SSH:");
            e.printStackTrace();
        }
    }
}