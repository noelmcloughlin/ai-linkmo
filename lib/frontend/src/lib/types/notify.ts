// notify.ts
// Types for notifications and the notification store.
export type NotificationType = "info" | "warning" | "error" | "success";

export type NotifyAction = {
  label: string;
  callback: () => void; // Function to execute when the action is clicked
};

export type Notify = {
  id?: string | number; // Optional ID for the notification
  type: NotificationType;
  message: string;
  duration?: number; // Optional duration for the notification
  actions?: NotifyAction[];
};

export type NotificationStore = {
  id?: number | string;
  type: NotificationType;
  message: string;
  duration?: number;
  notifications: Notify[];
};
