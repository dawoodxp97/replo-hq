
import React from "react";
import PropTypes from "prop-types";
import { Button as AntButton } from "antd";

/**
 * Replo Button — Ant Design wrapper component.
 *
 * Implements Ant Design Button variants: `primary`, `default`, `dashed`, `text`, `link`.
 * Supports standard props: `size`, `shape`, `loading`, `disabled`, `danger`, `ghost`, `block`, `htmlType`, `href`, `icon`, `className`, `style`.
 * Handles click events and passes any additional props through to Ant Design's Button.
 *
 * Responsive design: set `responsive` to true to make the button full width on small screens.
 *
 * @typedef {('primary'|'default'|'dashed'|'link'|'text')} ButtonType
 * @typedef {('small'|'middle'|'large')} ButtonSize
 * @typedef {('default'|'circle'|'round')} ButtonShape
 *
 * @param {Object} props
 * @param {ButtonType} [props.type='default'] Visual style variant
 * @param {ButtonSize} [props.size='middle'] Control size
 * @param {ButtonShape} [props.shape='default'] Shape of the button
 * @param {boolean} [props.loading=false] Loading state
 * @param {boolean} [props.disabled=false] Disable state
 * @param {boolean} [props.danger=false] Danger style
 * @param {boolean} [props.ghost=false] Ghost style
 * @param {boolean} [props.block=false] Full-width button
 * @param {React.ReactNode} [props.icon] Icon element per Ant Design specs
 * @param {'button'|'submit'|'reset'} [props.htmlType='button'] Native button type
 * @param {string} [props.href] Link target when using `type='link'`
 * @param {React.MouseEventHandler<HTMLButtonElement>} [props.onClick] Click handler
 * @param {string} [props.className] Additional class names
 * @param {React.CSSProperties} [props.style] Inline styles
 * @param {boolean} [props.responsive=false] Make button full width on small screens
 * @param {React.ReactNode} props.children Button content
 * @returns {React.ReactElement|null}
 *
 * @example
 * // Primary button with icon
 * // import { PlusOutlined } from '@ant-design/icons';
 * // <Button type="primary" icon={<PlusOutlined />} onClick={() => {}}>Create</Button>
 *
 * @example
 * // Link button
 * // <Button type="link" href="/docs">Docs</Button>
 */
const Button = ({
  type = "default",
  size = "middle",
  shape = "default",
  loading = false,
  disabled = false,
  danger = false,
  ghost = false,
  block = false,
  icon,
  htmlType = "button",
  href,
  onClick,
  className,
  style,
  responsive = false,
  children,
  ...rest
}) => {
  const responsiveClass = responsive ? "w-full sm:w-auto" : undefined;

  return (
    <AntButton
      type={type}
      size={size}
      shape={shape}
      loading={loading}
      disabled={disabled}
      danger={danger}
      ghost={ghost}
      block={block}
      icon={icon}
      htmlType={htmlType}
      href={href}
      onClick={onClick}
      className={[responsiveClass, className].filter(Boolean).join(" ")}
      style={style}
      {...rest}
    >
      {children}
    </AntButton>
  );
};

Button.propTypes = {
  type: PropTypes.oneOf(["primary", "default", "dashed", "link", "text"]),
  size: PropTypes.oneOf(["small", "middle", "large"]),
  shape: PropTypes.oneOf(["default", "circle", "round"]),
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
  danger: PropTypes.bool,
  ghost: PropTypes.bool,
  block: PropTypes.bool,
  icon: PropTypes.node,
  htmlType: PropTypes.oneOf(["button", "submit", "reset"]),
  href: PropTypes.string,
  onClick: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object,
  responsive: PropTypes.bool,
  children: PropTypes.node,
};

export default Button;

