// Implement a Notification Store
import type { NotificationStore, NotificationType, Notify } from "$types/notify";

class NotifyStore implements NotificationStore {
    id?: number | string = $state("");
    typeof: NotificationType = $state("info");
    message: string = $state("");
    duration: number = $state(3000); // delete duration
    notifications: Notify[] = $state([]);

    getAll() {
        return this.notifications;
    }

    add(notification: Notify) {
        this.id = notification.id || Date.now(); // Generate a unique ID if not provided
        this.notifications.push(notification);
        this.typeof = notification.typeof;
        this.message = notification.message;
        this.duration = notification.duration || 3000;
    }

    dismiss(id: number | string) {
        this.notifications = this.notifications.filter(notification => notification.id !== id);
    }

    resetAll() {
        this.id = "";
        this.notifications = [];
        this.typeof = "info";
        this.message = "";
        this.duration = 0;
    }
}
export const notifyStore = new NotifyStore();

export const notify = {
    subscribe: notifyStore.notifications,
    add: (notification: Notify) => notifyStore.add(notification),
    dismiss: (id: number | string) => notifyStore.dismiss(id),
    getAll: () => notifyStore.getAll(),
    resetAll: () => notifyStore.resetAll(),
    info: (message: string) => notifyStore.add({
        id: Date.now(),
        typeof: "info",
        message,
        duration: 3000
    }),
    error: (message: string) => notifyStore.add({
        id: Date.now(),
        typeof: "error",
        message,
        duration: 3000
    }),
    warning: (message: string) => notifyStore.add({
        id: Date.now(),
        typeof: "warning",
        message,
        duration: 3000
    }),
    success: (message: string) => notifyStore.add({
        id: Date.now(),
        typeof: "success",
        message,
        duration: 3000
    }),
};