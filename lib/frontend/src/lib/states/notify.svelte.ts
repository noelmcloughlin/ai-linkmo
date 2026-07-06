// Notification store implementation.
import type {
  NotificationStore,
  NotificationType,
  Notify,
} from "$types/notify";

// Monotonic counter so ids stay unique even within the same millisecond
let nextNotificationSeq = 0;

class NotifyStore implements NotificationStore {
  id?: number | string = $state("");
  type: NotificationType = $state("info");
  message: string = $state("");
  duration: number = $state(3000); // default duration (ms)
  notifications: Notify[] = $state([]);

  getAll() {
    return this.notifications;
  }

  add(notification: Notify) {
    // Every notification needs its own id, otherwise dismiss() cannot find it
    notification.id =
      notification.id ?? `n-${Date.now()}-${nextNotificationSeq++}`;
    this.id = notification.id;
    this.notifications.push(notification);
    this.type = notification.type;
    this.message = notification.message;
    this.duration = notification.duration || 3000;
  }

  dismiss(id: number | string) {
    this.notifications = this.notifications.filter(
      (notification) => notification.id !== id,
    );
  }

  resetAll() {
    this.id = "";
    this.notifications = [];
    this.type = "info";
    this.message = "";
    this.duration = 0;
  }
}
export const notifyStore = new NotifyStore();

export const notify = {
  add: (notification: Notify) => notifyStore.add(notification),
  dismiss: (id: number | string) => notifyStore.dismiss(id),
  getAll: () => notifyStore.getAll(),
  resetAll: () => notifyStore.resetAll(),
  info: (message: string) =>
    notifyStore.add({ type: "info", message, duration: 3000 }),
  error: (message: string) =>
    notifyStore.add({ type: "error", message, duration: 3000 }),
  warning: (message: string) =>
    notifyStore.add({ type: "warning", message, duration: 3000 }),
  success: (message: string) =>
    notifyStore.add({ type: "success", message, duration: 3000 }),
};
