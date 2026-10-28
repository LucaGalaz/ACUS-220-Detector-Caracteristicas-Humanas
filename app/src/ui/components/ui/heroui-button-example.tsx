"use client";

import { Button } from "@heroui/react";

export function ContinueButton({ onPress }: { onPress: () => void }) {
  return <Button onPress={onPress}>CONTINUAR</Button>;
}
