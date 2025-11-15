// Official Telegram SVG icon as a React component
interface TelegramIconProps {
  className?: string;
  color?: string;
}

export default function TelegramIcon({ className = '', color = '#229ED9' }: TelegramIconProps) {
  return (
    <svg className={className} viewBox="0 0 240 240" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="120" cy="120" r="120" fill={color} />
      <path d="M180.5 72.5L157.5 177.5C155.5 185.5 150.5 187.5 143.5 183.5L110.5 158.5L94.5 173.5C92.5 175.5 91 177 87.5 177L90.5 142.5L159.5 81.5C162.5 78.5 159.5 77.5 155.5 80.5L77.5 132.5L43.5 121.5C36.5 119.5 36.5 114.5 45.5 111.5L172.5 67.5C178.5 65.5 183.5 69.5 180.5 72.5Z" fill="white"/>
    </svg>
  );
}
