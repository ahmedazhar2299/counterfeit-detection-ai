import { motion } from 'framer-motion'
import { History, LineChart, Shield } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { BrandMark } from './brand-mark'
import { ThemeToggle } from './theme-toggle'

const links = [
  { to: '/', label: 'Analyze', icon: Shield },
  { to: '/history', label: 'History', icon: History },
  { to: '/metrics', label: 'Metrics', icon: LineChart }
]

export function TopNav() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/20 bg-white/30 backdrop-blur-xl dark:bg-slate-950/30">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-primary/90 p-2 text-primary-foreground">
            <BrandMark className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-semibold leading-tight">CounterfeitGuard</p>
            <p className="text-xs text-muted-foreground">Counterfeit Risk Intelligence</p>
          </div>
        </div>

        <nav className="flex items-center gap-2">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} className="relative px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground">
              {({ isActive }) => (
                <>
                  <span className="inline-flex items-center gap-2">
                    <link.icon className="h-4 w-4" />
                    {link.label}
                  </span>
                  {isActive && <motion.span layoutId="active-nav" className="absolute -bottom-1 left-2 right-2 h-0.5 rounded-full bg-primary" />}
                </>
              )}
            </NavLink>
          ))}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
