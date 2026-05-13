
// Define a typeof from UI dropdown options
export interface DropdownOptionType {
  label: string;
  value: string;
  [key: string]: string | unknown;
}

// Define a typeof from UI field objects
export interface FieldType {
  key: string;
  value: {
    description?: string;
    type?: string;
    [prop: string]: unknown;
  };
}