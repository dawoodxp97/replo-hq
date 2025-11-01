'use client';

import React, { forwardRef, useMemo } from 'react';
import { Input, InputNumber } from 'antd';

const { TextArea, Search, Password } = Input;

/**
 * Ant Design compatible sizes
 */
export type InputSize = 'small' | 'middle' | 'large';

/**
 * Visual appearance variants per Ant Design v5
 */
export type InputAppearance =
  | 'outlined'
  | 'borderless'
  | 'filled'
  | 'underlined';

/**
 * Supported input kinds wrapped by this component
 */
export type InputKind =
  | 'text'
  | 'textarea'
  | 'search'
  | 'password'
  | 'number'
  | 'email';

/**
 * JSDoc helper for showCount formatter
 */
export interface CountInfo {
  value: string;
  count: number;
  maxLength?: number;
}

/**
 * Common props across all variants
 *
 * - Covers Ant Design specific props (size, allowClear, bordered, status, variant)
 * - Adds accessibility and responsive helpers
 */
export interface CommonInputProps {
  /** Which input variant to render */
  kind?: InputKind;
  /** Visual size per Ant Design */
  size?: InputSize;
  /** Whether input is disabled */
  disabled?: boolean;
  /** Allow clear icon to reset the content */
  allowClear?: boolean | { clearIcon?: React.ReactNode };
  /** Border style control (prefer `appearance`) */
  bordered?: boolean;
  /** Validation status for error/warning styling */
  status?: 'error' | 'warning';
  /** Ant Design appearance variant */
  appearance?: InputAppearance;
  /** HTML required attribute for form validation */
  required?: boolean;
  /** Optional prefix icon/node */
  prefix?: React.ReactNode;
  /** Optional suffix icon/node */
  suffix?: React.ReactNode;
  /** Optional addon before input */
  addonBefore?: React.ReactNode;
  /** Optional addon after input */
  addonAfter?: React.ReactNode;
  /** Custom className (supports responsive helper) */
  className?: string;
  /** Custom inline styles */
  style?: React.CSSProperties;
  /** When true: full width on small screens */
  responsive?: boolean;
  /** Accessible label for screen readers */
  'aria-label'?: string;
  /** Element id */
  id?: string;
}

/**
 * Props for basic text input
 */
export interface TextInputProps extends CommonInputProps {
  /** Whether to show title */
  showTitle?: boolean;
  /** Title text */
  title?: string;
  kind?: 'text';
  /** Value for controlled input */
  value?: string;
  /** Default value for uncontrolled input */
  defaultValue?: string;
  /** Change handler */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /** Enter press handler */
  onPressEnter?: React.KeyboardEventHandler<HTMLInputElement>;
  /** Placeholder text */
  placeholder?: string;
  /** HTML input type, e.g. text, email */
  type?: React.HTMLInputTypeAttribute;
  /** Max character length */
  maxLength?: number;
  /** Display character count */
  showCount?: boolean | { formatter?: (info: CountInfo) => React.ReactNode };
  /** Auto-complete attribute */
  autoComplete?: string;
  /** Submit handler */
  onSubmitCapture?: React.FormEventHandler<HTMLFormElement>;
}

/**
 * Props for multi-line TextArea
 */
export interface TextAreaInputProps extends CommonInputProps {
  kind: 'textarea';
  /** Value for controlled TextArea */
  value?: string;
  /** Default value for uncontrolled TextArea */
  defaultValue?: string;
  /** Change handler */
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement>;
  /** Placeholder text */
  placeholder?: string;
  /** Rows when autoSize=false */
  rows?: number;
  /** Auto size configuration */
  autoSize?: boolean | { minRows?: number; maxRows?: number };
  /** Max character length */
  maxLength?: number;
  /** Display character count */
  showCount?: boolean | { formatter?: (info: CountInfo) => React.ReactNode };
}

/**
 * Props for Search input
 */
export interface SearchInputProps extends CommonInputProps {
  kind: 'search';
  /** Value for controlled input */
  value?: string;
  /** Default value for uncontrolled input */
  defaultValue?: string;
  /** Change handler */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /** Placeholder text */
  placeholder?: string;
  /** Show default or primary button or provide custom node */
  enterButton?: boolean | React.ReactNode;
  /** Loading state for search */
  loading?: boolean;
  /** Triggered on click search, clear icon, or press Enter */
  onSearch?: (
    value: string,
    event?:
      | React.ChangeEvent<HTMLInputElement>
      | React.MouseEvent<HTMLElement>
      | React.KeyboardEvent<HTMLInputElement>,
    info?: { source: 'input' | 'clear' }
  ) => void;
}

/**
 * Props for Email input
 */
export interface EmailInputProps extends CommonInputProps {
  title?: string;

  kind: 'email';
  /** Value for controlled input */
  value?: string;
  /** Default value for uncontrolled input */
  defaultValue?: string;
  /** Change handler */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /** Placeholder text */
  placeholder?: string;
  /** Toggle visibility or control visibility */
  visibilityToggle?:
    | boolean
    | { visible?: boolean; onVisibleChange?: (visible: boolean) => void };
  /** Custom eye icon renderer */
  iconRender?: (visible: boolean) => React.ReactNode;
}

/**
 * Props for Password input
 */
export interface PasswordInputProps extends CommonInputProps {
  kind: 'password';
  /** Value for controlled input */
  value?: string;
  /** Default value for uncontrolled input */
  defaultValue?: string;
  /** Change handler */
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  /** Placeholder text */
  placeholder?: string;
  /** Toggle visibility or control visibility */
  visibilityToggle?:
    | boolean
    | { visible?: boolean; onVisibleChange?: (visible: boolean) => void };
  /** Custom eye icon renderer */
  iconRender?: (visible: boolean) => React.ReactNode;
}

/**
 * Props for numeric input (InputNumber)
 */
export interface NumberInputProps
  extends Omit<
    CommonInputProps,
    'prefix' | 'suffix' | 'addonBefore' | 'addonAfter'
  > {
  kind: 'number';
  /** Value for controlled numeric input */
  value?: number;
  /** Default value for uncontrolled numeric input */
  defaultValue?: number;
  /** Change handler returns number or null when cleared */
  onChange?: (value: number | null) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Minimum value */
  min?: number;
  /** Maximum value */
  max?: number;
  /** Increment step */
  step?: number;
  /** Decimal precision */
  precision?: number;
  /** Format displayed value (stringMode aware) */
  formatter?: (value: number | string | undefined) => string;
  /** Parse display back into value */
  parser?: (displayValue: string | undefined) => number;
  /** Use string mode for high precision numbers */
  stringMode?: boolean;
}

export type ReploInputProps =
  | TextInputProps
  | TextAreaInputProps
  | SearchInputProps
  | PasswordInputProps
  | NumberInputProps
  | EmailInputProps;

/**
 * Replo Input — Ant Design wrapper component.
 *
 * Supports: `text`, `textarea`, `search`, `password`, `number`.
 * Implements Ant Design props like `size`, `allowClear`, `bordered`, `status`, `appearance`,
 * and input-specific props including `rows`, `autoSize`, `visibilityToggle`, etc.
 *
 * Accessibility: sets `aria-invalid` when `status='error'`. If `aria-label` is absent,
 * uses `placeholder` as a fallback screen-reader label for simple cases.
 *
 * Responsive: when `responsive` is true, the input is full width on small screens.
 */
const ReploInput = forwardRef<unknown, ReploInputProps>((props, ref) => {
  const {
    // Common
    kind = 'text',
    size = 'middle',
    disabled = false,
    allowClear = false,
    bordered = true,
    status,
    appearance = 'outlined',

    className,
    style,
    responsive = false,
    id,
    required,
    'aria-label': ariaLabel,
    // Specific ones will be in rest
    ...rest
  } = props as ReploInputProps;

  // Memoize class composition for performance
  const composedClassName = useMemo(() => {
    const responsiveClass = responsive ? 'w-full sm:w-auto' : undefined;
    return [responsiveClass, className].filter(Boolean).join(' ');
  }, [responsive, className]);

  // Accessibility: compute aria-invalid and label fallback
  const ariaInvalid: boolean | undefined =
    status === 'error' ? true : undefined;
  const computedAriaLabel =
    ariaLabel ??
    ('placeholder' in rest ? (rest as any).placeholder : undefined);

  // Guard: warn when using addon/prefix/suffix with kind='number' (unsupported on InputNumber)
  const decorators = props as CommonInputProps;
  if (
    kind === 'number' &&
    (decorators.prefix ||
      decorators.suffix ||
      decorators.addonBefore ||
      decorators.addonAfter)
  ) {
    // eslint-disable-next-line no-console
    console.warn(
      "ReploInput: prefix/suffix/addonBefore/addonAfter are not supported with kind='number' (InputNumber)."
    );
  }

  // Render by kind
  switch (kind) {
    case 'textarea': {
      const ta = rest as TextAreaInputProps;
      return (
        <TextArea
          ref={ref as any}
          size={size}
          disabled={disabled}
          allowClear={allowClear as boolean}
          bordered={bordered}
          status={status}
          variant={appearance}
          className={composedClassName}
          style={style}
          id={id}
          required={required}
          aria-label={computedAriaLabel}
          aria-invalid={ariaInvalid}
          // Specific
          value={ta.value}
          defaultValue={ta.defaultValue}
          onChange={ta.onChange}
          placeholder={ta.placeholder}
          rows={ta.rows}
          autoSize={ta.autoSize}
          maxLength={ta.maxLength}
          showCount={ta.showCount as any}
        />
      );
    }
    case 'search': {
      const s = rest as SearchInputProps;
      return (
        <Search
          ref={ref as any}
          size={size}
          disabled={disabled}
          allowClear={allowClear as boolean}
          bordered={bordered}
          status={status}
          variant={appearance}
          className={composedClassName}
          style={style}
          id={id}
          required={required}
          aria-label={computedAriaLabel}
          aria-invalid={ariaInvalid}
          // Specific
          value={s.value}
          defaultValue={s.defaultValue}
          onChange={s.onChange}
          placeholder={s.placeholder}
          enterButton={s.enterButton}
          loading={s.loading}
          onSearch={s.onSearch as any}
          prefix={(props as CommonInputProps).prefix}
          suffix={(props as CommonInputProps).suffix}
          addonBefore={(props as CommonInputProps).addonBefore}
          addonAfter={(props as CommonInputProps).addonAfter}
        />
      );
    }
    case 'email': {
      const t = rest as TextInputProps;
      return (
        <div>
          {t?.title && (
            <label
              data-slot="label"
              htmlFor={id}
              className="pb-2 flex items-center gap-2 text-sm leading-none font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50"
            >
              {t?.title}
            </label>
          )}
          <Input
            data-slot="input"
            ref={ref as any}
            size={size}
            disabled={disabled}
            allowClear={allowClear as boolean}
            status={status}
            variant={appearance}
            className={composedClassName}
            style={style}
            id={id}
            required={required}
            aria-label={computedAriaLabel}
            aria-invalid={ariaInvalid}
            value={t.value}
            defaultValue={t.defaultValue}
            onChange={t.onChange}
            onPressEnter={t.onPressEnter}
            placeholder={t.placeholder || 'Please enter your email'}
            type={'email'}
            onSubmitCapture={e => {
              e.preventDefault();
              t?.onSubmitCapture?.(
                e as unknown as React.FormEvent<HTMLFormElement>
              );
              console.log('onSubmitCapture', e);
            }}
          />
        </div>
      );
    }
    case 'password': {
      const p = rest as PasswordInputProps;
      return (
        <Password
          ref={ref as any}
          size={size}
          disabled={disabled}
          allowClear={allowClear as boolean}
          bordered={bordered}
          status={status}
          variant={appearance}
          className={composedClassName}
          style={style}
          id={id}
          required={required}
          aria-label={computedAriaLabel}
          aria-invalid={ariaInvalid}
          // Specific
          value={p.value}
          defaultValue={p.defaultValue}
          onChange={p.onChange}
          placeholder={p.placeholder}
          visibilityToggle={p.visibilityToggle as any}
          iconRender={p.iconRender}
          prefix={(props as CommonInputProps).prefix}
          suffix={(props as CommonInputProps).suffix}
          addonBefore={(props as CommonInputProps).addonBefore}
          addonAfter={(props as CommonInputProps).addonAfter}
        />
      );
    }
    case 'number': {
      const n = rest as NumberInputProps;
      return (
        <InputNumber
          ref={ref as any}
          size={size}
          disabled={disabled}
          bordered={bordered}
          status={status}
          className={composedClassName}
          style={style}
          id={id}
          aria-label={computedAriaLabel}
          aria-invalid={ariaInvalid}
          // Specific
          value={n.value as any}
          defaultValue={n.defaultValue as any}
          onChange={n.onChange}
          placeholder={n.placeholder}
          min={n.min}
          max={n.max}
          step={n.step}
          precision={n.precision}
          formatter={n.formatter as any}
          parser={n.parser as any}
          stringMode={n.stringMode}
        />
      );
    }
    case 'text':
    default: {
      const t = rest as TextInputProps;
      return (
        <Input
          ref={ref as any}
          size={size}
          disabled={disabled}
          allowClear={allowClear as boolean}
          bordered={bordered}
          status={status}
          variant={appearance}
          className={composedClassName}
          style={style}
          id={id}
          required={required}
          aria-label={computedAriaLabel}
          aria-invalid={ariaInvalid}
          // Specific
          value={t.value}
          defaultValue={t.defaultValue}
          onChange={t.onChange}
          onPressEnter={t.onPressEnter}
          placeholder={t.placeholder}
          type={t.type}
          maxLength={t.maxLength}
          showCount={t.showCount as any}
          autoComplete={t.autoComplete}
          prefix={(props as CommonInputProps).prefix}
          suffix={(props as CommonInputProps).suffix}
          addonBefore={(props as CommonInputProps).addonBefore}
          addonAfter={(props as CommonInputProps).addonAfter}
        />
      );
    }
  }
});

ReploInput.displayName = 'ReploInput';

export default React.memo(ReploInput);
