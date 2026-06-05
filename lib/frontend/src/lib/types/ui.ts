// Type for UI dropdown options.
export interface DropdownOptionType {
  label: string;
  value: string;
  [key: string]: string | unknown;
}

// Type for UI field objects.
export interface FieldType {
  key: string;
  value: {
    description?: string;
    type?: string;
    [prop: string]: unknown;
  };
}
