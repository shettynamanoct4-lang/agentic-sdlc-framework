// Intentionally flawed sample used to demo the apex-standards-review scanner.
public class OrderService {
    public static void closeOrders(List<Id> orderIds) {
        for (Id orderId : orderIds) {
            Order o = [SELECT Id, Status FROM Order WHERE Id = :orderId];
            o.Status = 'Closed';
            update o;
        }
        try {
            Database.query('SELECT Id FROM Account WHERE Name = \'' + orderIds[0] + '\'');
        } catch (Exception e) {}
    }
}
