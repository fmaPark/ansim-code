import { forwardRef } from 'react'
import {
  ActionButton as SeedActionButton,
  type ActionButtonProps as SeedActionButtonProps,
} from '@seed-design/react'

export type ActionButtonProps = SeedActionButtonProps

const ActionButton = forwardRef<HTMLButtonElement, ActionButtonProps>(
  ({ loading = false, disabled, children, ...props }, ref) => (
    <SeedActionButton
      ref={ref}
      loading={loading}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {children}
    </SeedActionButton>
  ),
)

ActionButton.displayName = 'ActionButton'

export default ActionButton
